from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
from utilities import get_user_info_external, get_user_info_external_by_input, \
    get_thread_info_external_params, get_thread_info_external, get_forum_info_external, true_false_ret, zero_check
import datetime, json

forum_api = Blueprint('forum_api', __name__)
mysql = MySQL()


@forum_api.route('create/', methods=['POST'])
def forum_create():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('name' in req_json and 'short_name' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_name = req_json['name']
    new_short_name = req_json['short_name']
    new_user = req_json['user']

    sql_data = (new_name, new_short_name, new_user)
    try:
        cursor.execute('INSERT INTO Forum VALUES (null,%s,%s,%s)', sql_data)
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")

    resp = {
        "id": cursor.lastrowid,
        "name": new_name,
        "short_name": new_short_name,
        "user": new_user
    }
    return jsonify(code=0, response=resp)


@forum_api.route('details/', methods=['GET'])
def forum_details():
    conn = mysql.get_db()
    cursor = conn.cursor()
    forum_short_name = request.args.get('forum')

    if not forum_short_name:
        return jsonify(code=3, response="Wrong request")

    try:
        cursor.execute("SELECT * FROM Forum WHERE short_name='%s'" % forum_short_name)
    except Exception:
        return jsonify(code=3, response="Wrong request")
    forum = cursor.fetchall()
    if not forum:
        return jsonify(code=1, response="No such thread")

    forum_info = forum[0]
    forum_id = forum_info[0]
    forum_name = forum_info[1]
    forum_short_name = forum_info[2]
    user_email = forum_info[3]

    if request.args.get('related') == 'user':
        user_info = get_user_info_external(cursor, user_email)
    else:
        user_info = user_email

    resp = {
        "id": forum_id,
        "name": forum_name,
        "short_name": forum_short_name,
        "user": user_info
    }
    return jsonify(code=0, response=resp)


@forum_api.route('listThreads/', methods=['GET'])
def forum_list_threads():
    forum_short_name = request.args.get('forum')
    if not forum_short_name:
        return jsonify(code=3, response="Wrong request")

    since = request.args.get('since')
    if not since:
        since = "1970-01-01 00:00:00"

    limit = ""
    if request.args.get('limit'):
        limit = "LIMIT " + request.args.get('limit')

    order = request.args.get('order')
    if not order:
        order = "DESC"
    related_list = request.args.getlist('related')

    return get_thread_info_external_params(forum_short_name, since, limit, order, related_list)


@forum_api.route('listUsers/', methods=['GET'])
def forum_list_users():
    conn = mysql.get_db()
    cursor = conn.cursor()
    forum_short_name = request.args.get('forum')
    if not forum_short_name:
        return jsonify(code=3, response="Wrong request")

    since_id = request.args.get('since_id')
    if not since_id:
        since_id = 0

    limit = ""
    if request.args.get('limit'):
        limit = "LIMIT " + request.args.get('limit')

    order = request.args.get('order')
    if not order:
        order = "DESC"

    full_query = "SELECT DISTINCT(P.user), U.id, U.email, U.about, U.isAnonymous, U.name, U.username FROM Post P " \
                 "INNER JOIN User U ON P.user=U.email WHERE P.isDeleted=0 AND P.forum='%s' AND U.id >= '%s' " \
                 "ORDER BY U.name %s %s" % (forum_short_name, since_id, order, limit)

    cursor.execute(full_query)
    user_info = cursor.fetchall()
    if not user_info:
        return jsonify(code=0, response=[])
    end_list = []
    for x in user_info:
        end_list.append(get_user_info_external_by_input(cursor, x))
    return jsonify(code=0, response=end_list)


@forum_api.route('listPosts/', methods=['GET'])
def forum_list_posts():
    conn = mysql.get_db()
    cursor = conn.cursor()
    forum_short_name = request.args.get('forum')
    if not forum_short_name:
        return jsonify(code=3, response="Wrong request")

    since = request.args.get('since')
    if not since:
        since = "1970-01-01"

    limit = ""
    if request.args.get('limit'):
        limit = "LIMIT " + str(request.args.get('limit'))

    order = request.args.get('order')
    if not order:
        order = "DESC"

    related_list = request.args.getlist('related')

    query_first = "SELECT P.id, P.date, P.thread, P.message, P.user, P.forum, P.parent, P.isApproved, P.isHighlighted, " \
                  "P.isEdited, P.isSpam, P.isDeleted, P.likes, P.dislikes, P.points, P.path FROM Post P " \
                  "INNER JOIN Forum F ON P.forum=F.short_name WHERE F.short_name='%s' AND P.date >= '%s' " \
                  "ORDER BY P.date %s %s" % (forum_short_name, since, order, limit)
    cursor.execute(query_first)
    posts_info = cursor.fetchall()
    if not posts_info:
        return jsonify(code=0, response=[])
    end_list = []
    for x in posts_info:
        end_list.append(get_post_info_params(cursor, x, related_list))
    return jsonify(code=0, response=end_list)


def get_post_info_params(cursor, post_info, related_list):
    user_info = post_info[4]
    thread_info = post_info[2]
    forum_info = post_info[5]
    for related in related_list:
        if related == 'user':
            user_info = get_user_info_external(cursor, post_info[4])
        elif related == 'thread':
            thread_info = get_thread_info_external(cursor, post_info[2])
        elif related == 'forum':
            forum_info = get_forum_info_external(cursor, post_info[5])

    resp = {
        "date": datetime.datetime.strftime(post_info[1], "%Y-%m-%d %H:%M:%S"),
        "dislikes": post_info[13],
        "forum": forum_info,
        "id": post_info[0],
        "isApproved": true_false_ret(post_info[7]),
        "isDeleted": true_false_ret(post_info[11]),
        "isEdited": true_false_ret(post_info[9]),
        "isHighlighted": true_false_ret(post_info[8]),
        "isSpam": true_false_ret(post_info[10]),
        "likes": post_info[12],
        "message": post_info[3],
        "parent": zero_check(post_info[6]),
        "points": post_info[14],
        "thread": thread_info,
        "user": user_info
    }
    return resp




