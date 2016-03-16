from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import re, datetime
import json
from utilities import get_user_info_external, get_forum_info_external, \
    get_thread_info_external, get_post_info_by_post, true_false_ret


post_api = Blueprint('post_api', __name__)
mysql = MySQL()


@post_api.route('create/', methods=['POST'])
def post_create():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('date' in req_json and 'thread' in req_json and 'message' in req_json
            and 'user' in req_json and 'forum' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_post_date = req_json['date']
    new_post_thread_id = req_json['thread']
    new_post_message = req_json['message']
    new_post_user_email = req_json['user']
    new_post_forum_short_name = req_json['forum']
    new_post_is_approved = 0
    new_post_is_high = 0
    new_post_is_edited = 0
    new_post_is_spam = 0
    new_post_is_del = 0
    new_post_parent_id = 0

    if 'parent' in req_json and req_json['parent'] is not None:
        new_post_parent_id = req_json['parent']
    new_post_path = get_post_path(cursor, new_post_parent_id)

    if 'isApproved' in req_json and req_json['isApproved']:
            new_post_is_approved = 1
    if 'isHighlighted' in req_json and req_json['isHighlighted']:
            new_post_is_high = 1
    if 'isEdited' in req_json and req_json['isEdited']:
        new_post_is_edited = 1
    if 'isSpam' in req_json and req_json['isSpam']:
        new_post_is_spam = 1
    if 'isDeleted' in req_json and req_json['isDeleted']:
        new_post_is_del = 1

    sql_data = (new_post_date, new_post_thread_id, new_post_message, new_post_user_email, new_post_forum_short_name,
                new_post_parent_id, new_post_is_approved, new_post_is_high, new_post_is_edited, new_post_is_spam,
                new_post_is_del, new_post_path)
    try:
        cursor.execute("INSERT INTO Post VALUES (null,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,%s)", sql_data)
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")
    resp = {
        "date": new_post_date,
        "forum": new_post_forum_short_name,
        "id": cursor.lastrowid,
        "isApproved": true_false_ret(new_post_is_approved),
        "isDeleted": true_false_ret(new_post_is_del),
        "isEdited": true_false_ret(new_post_is_edited),
        "isHighlighted": true_false_ret(new_post_is_high),
        "isSpam": true_false_ret(new_post_is_spam),
        "message": new_post_message,
        "parent": zero_check(new_post_parent_id),
        "thread": new_post_thread_id,
        "user": new_post_user_email,
        "likes": 0,
        "dislikes": 0,
        "points": 0
    }
    return jsonify(code=0, response=resp)


def zero_check(value):
    if int(value) == 0:
        return None
    return value


@post_api.route('details/', methods=['GET'])
def post_details():
    conn = mysql.get_db()
    cursor = conn.cursor()
    post_id = request.args.get('post')
    if not post_id:
        return jsonify(code=3, response="Wrong request")
    if int(post_id) < 0:
        cursor.execute("SELECT max(id) FROM Post")
        info = cursor.fetchall()
        if info:
            post_id = int(info[0][0]) + int(post_id) + 1
    try:
        cursor.execute("SELECT * FROM Post WHERE id='%s'" % post_id)
    except Exception:
         return jsonify(code=3, response="Wrong request")
    post = cursor.fetchall()
    if not post:
        return jsonify(code=1, response="User doesn't exist")
    post_info = post[0]
    thread_info = post_info[2]
    user_info = post_info[4]
    forum_info = post_info[5]
    related = request.args.getlist('related')
    if 'user' in related:
        user_info = get_user_info_external(cursor, post_info[4])
    if 'forum' in related:
        forum_info = get_forum_info_external(cursor, post_info[5])
    if 'thread' in related:
        thread_info = get_thread_info_external(cursor, post_info[2])

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
    return jsonify(code=0, response=resp)


@post_api.route('list/', methods=['GET'])
def post_list():
    conn = mysql.get_db()
    cursor = conn.cursor()
    forum_short_name = request.args.get('forum')
    thread_id = request.args.get('thread')
    if not (forum_short_name or thread_id):
        return jsonify(code=3, response="Wrong request")

    since = request.args.get('since')
    if not since:
        since = "1970-01-01"

    limit = ""
    if request.args.get('limit'):
        limit = "LIMIT " + request.args.get('limit')

    order = request.args.get('order')
    if not order:
        order = "DESC"

    if forum_short_name:
        query_first = "SELECT * FROM Post WHERE forum='%s'" % forum_short_name
    elif thread_id:
        query_first = "SELECT * FROM Post WHERE thread='%s'" % thread_id
    query_second = " AND date >= '%s' ORDER BY date %s %s" % (since, order, limit)
    full_query = query_first + query_second
    try:
        cursor.execute(full_query)
    except Exception:
        return jsonify(code=3, response="Wrong request")

    all_posts = cursor.fetchall()
    if not all_posts:
        return jsonify(code=0, response={})
    end_list = []
    for x in all_posts:
        end_list.append(get_post_info_by_post(cursor, x))
    return jsonify(code=0, response=end_list)


@post_api.route('remove/', methods=['POST'])
def post_set_deleted():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json):
        return jsonify(code=3, response="Wrong request")

    post_id = req_json['post']
    return open_close_post(1, post_id)


@post_api.route('restore/', methods=['POST'])
def post_set_active():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json):
        return jsonify(code=3, response="Wrong request")

    post_id = req_json['post']
    return open_close_post(0, post_id)


@post_api.route('update/', methods=['POST'])
def post_update():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")
    if not ('post' in req_json and 'message' in req_json):
        return jsonify(code=3, response="Wrong request")
    post_id = req_json['post']
    new_message = req_json['message']
    cursor.execute("UPDATE Post SET message=%s WHERE id=%s", (new_message, post_id))
    conn.commit()
    cursor.execute("SELECT * FROM Post WHERE id='%s'" % post_id)
    post_info = cursor.fetchall()[0]
    if not post_info:
        return jsonify(code=1, response="Can't find this post")
    resp = get_post_info_by_post(cursor, post_info)
    return jsonify(code=0, response=resp)


@post_api.route('vote/', methods=['POST'])
def post_vote():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json and 'vote' in req_json):
        return jsonify(code=3, response="Wrong request")
    post_id = req_json['post']
    vote_value = req_json['vote']

    cursor.execute("SELECT likes, dislikes, points FROM Post WHERE id='%s'" % post_id)
    likes_info = cursor.fetchall()
    if not likes_info:
        return jsonify(code=1, response="No such thread")
    likes = likes_info[0][0]
    dislikes = likes_info[0][1]
    points = likes_info[0][2]
    if vote_value == 1:
        likes += 1
        points += 1
    elif vote_value == -1:
        dislikes += 1
        points -= 1
    else:
        return jsonify(code=3, response="Wrong request")
    sql_update = (likes, dislikes, points, post_id)
    cursor.execute("UPDATE Post SET likes=%s, dislikes=%s, points=%s WHERE id=%s", sql_update)
    conn.commit()
    cursor.execute("SELECT * FROM Post WHERE id='%s'" % post_id)
    updated_thread = cursor.fetchall()
    resp = get_post_info_by_post(cursor, updated_thread[0])
    return jsonify(code=0, response=resp)


def open_close_post(is_del, post_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Post WHERE id='%s'" % post_id)
    if not cursor.fetchall():
         return jsonify(code=1, response="Can't find this post")
    cursor.execute("UPDATE Post SET isDeleted=%s WHERE id=%s", (is_del, post_id))
    conn.commit()
    resp = {
        "post": post_id
    }
    cursor.close()
    return jsonify(code=0, response=resp)


def get_post_path(cursor, new_post_parent_id):
    cursor.execute("SELECT path FROM Post WHERE id='%s'" % new_post_parent_id)
    info = cursor.fetchall()
    if info:
        parent_path = info[0][0]
        query_sub_path = parent_path + '.______'
        cursor.execute("SELECT max(path) FROM Post WHERE path LIKE '%s'" % query_sub_path)
        biggest_child_path = cursor.fetchall()[0][0]
        str_end = ""
        if biggest_child_path:
            biggest_child_path_list = re.findall('\d+', biggest_child_path)
            biggest_child_leaf_id = int(biggest_child_path_list[-1])
            new_post_leaf_id = biggest_child_leaf_id + 1
            for x in range(0, len(biggest_child_path_list)-1):
                str_end += str(biggest_child_path_list[x]) + '.'
            str_end += '{0:06d}'.format(int(new_post_leaf_id))
        else:
            add_path = '.{0:06d}'.format(1)
            str_end = parent_path + add_path
        new_post_path = str_end

    else:
        cursor.execute("SELECT max(path) FROM Post WHERE path LIKE '______'")
        biggest_post = cursor.fetchall()[0][0]
        if biggest_post is not None:
            biggest_post_id = int(biggest_post) + 1
            new_post_path = '{0:06d}'.format(biggest_post_id)
        else:
            new_post_path = '{0:06d}'.format(1)
    return new_post_path
