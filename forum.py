from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
from user import get_user_info_external, get_user_info_external_params
import datetime

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
        newId = cursor.lastrowid
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")

    resp = {
        "id": newId,
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

    if request.args.get('related', '') == 'user':
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
    related = request.args.get('related')

    return get_thread_info_external(forum_short_name, since, limit, order, related)


@forum_api.route('listUsers/', methods=['GET'])
def forum_list_users():
    forum_short_name = request.args.get('forum')
    if not forum_short_name:
        return jsonify(code=3, response="Wrong request")

    since_id = request.args.get('since_id')
    if not since_id:
        since_id = 1

    limit = ""
    if request.args.get('limit'):
        limit = "LIMIT " + request.args.get('limit')

    order = request.args.get('order')
    if not order:
        order = "DESC"
    return get_user_info_external_params(forum_short_name, limit, order, since_id)
    ####from posts!!!!!



def get_forum_info_external(cursor, forum_short_name):
    cursor.execute("SELECT * FROM Forum WHERE short_name='%s'" % forum_short_name)
    forum_info = cursor.fetchall()[0]
    resp = {}
    if forum_info:
        forum_id = forum_info[0]
        forum_name = forum_info[1]
        forum_short_name = forum_info[2]
        user_email = forum_info[3]

        resp = {
            "id": forum_id,
            "name": forum_name,
            "short_name": forum_short_name,
            "user": user_email
        }
    return resp


def get_thread_info_external(forum_short_name, since, limit, order, related):
    conn = mysql.get_db()
    cursor = conn.cursor()
    query_first = "SELECT * FROM Thread WHERE forum='%s'" % forum_short_name
    query_second = " AND date >= '%s'" % since
    query_third = " ORDER BY date %s %s" % (order, limit)
    full_query = query_first + query_second + query_third
    cursor.execute(full_query)
    thread = cursor.fetchall()
    if not thread:
        return jsonify(code=1, response="No such thread")
    end_list = []
    for x in thread:
        end_list.append(get_thread_with_params(cursor, x, related))
    return jsonify(code=0, response=end_list)


def get_thread_with_params(cursor, thread, related):
    thread_id = thread[0]
    thread_forum = thread[1]
    thread_title = thread[2]
    thread_is_closed = thread[3]
    thread_user = thread[4]
    thread_date = datetime.datetime.strftime(thread[5], "%Y-%m-%d %H:%M:%S")
    thread_msg = thread[6]
    thread_slug = thread[7]
    thread_is_del = thread[8]
    thread_likes = thread[9]
    thread_dislikes = thread[10]
    thread_points = thread[11]

    user_info = thread_user
    forum_info = thread_forum
    if related:
        if related == 'user':
            user_info = get_user_info_external(cursor, thread_user)

        elif related == 'forum':
            forum_info = get_forum_info_external(cursor, thread_forum)

    is_closed = False
    if thread_is_closed:
        is_closed = True

    is_del = False
    if thread_is_del:
        is_del = True

    resp = {
        "id": thread_id,
        "forum": forum_info,
        "title": thread_title,
        "isClosed": is_closed,
        "user": user_info,
        "date": thread_date,
        "message": thread_msg,
        "slug": thread_slug,
        "isDeleted": is_del,
        "likes": thread_likes,
        "dislikes": thread_dislikes,
        "points": thread_points
    }
    return resp