from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import datetime, time
from utilities import get_user_info_external, get_forum_info_external, get_post_info_by_post,true_false_ret, get_thread_info


thread_api = Blueprint('thread_api', __name__)
mysql = MySQL()


@thread_api.route('create/', methods=['POST'])
def thread_create():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('forum' in req_json and 'title' in req_json and 'isClosed' in req_json and 'user' in req_json and
                    'date' in req_json and 'message' in req_json and 'slug' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_thread_forum = req_json['forum']
    new_thread_title = req_json['title']
    new_thread_is_closed = req_json['isClosed']
    new_thread_user = req_json['user']
    new_thread_date = req_json['date']
    new_thread_msg = req_json['message']
    new_thread_slug = req_json['slug']
    new_thread_is_del = False

    new_thread_is_del_figure = 0
    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is True:
            new_thread_is_del = True
            new_thread_is_del_figure = 1

    new_thread_is_closed_figure = 0
    if new_thread_is_closed:
        new_thread_is_closed_figure = 1

    sql_data = (new_thread_forum, new_thread_title, new_thread_is_closed_figure, new_thread_user, new_thread_date,
                new_thread_msg, new_thread_slug, new_thread_is_del_figure, 0, 0, 0)
    try:
        cursor.execute('INSERT INTO Thread VALUES (null,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', sql_data)
        newId = cursor.lastrowid
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")

    resp = {
        "id": newId,
        "forum": new_thread_forum,
        "title": new_thread_title,
        "isClosed": new_thread_is_closed,
        "user": new_thread_user,
        "date": new_thread_date,
        "message": new_thread_msg,
        "slug": new_thread_slug,
        "isDeleted": new_thread_is_del
    }
    cursor.close()
    return jsonify(code=0, response=resp)


@thread_api.route('details/', methods=['GET'])
def thread_details():
    conn = mysql.get_db()
    cursor = conn.cursor()
    if not request.args.get('thread', ''):
        return jsonify(code=3, response="Wrong request")

    thread_id = request.args.get('thread', '')
    try:
        cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    except Exception:
        return jsonify(code=3, response="Wrong request")

    thread = cursor.fetchall()
    if not thread:
        return jsonify(code=1, response="No such thread")
    thread_info = thread[0]

    forum_info = thread_info[1]
    user_info = thread_info[4]
    arg = request.args.get('related')
    if arg:
        if arg == 'user':
            user_info = get_user_info_external(cursor, thread_info[4])
        elif arg == 'forum':
            forum_info = get_forum_info_external(cursor, thread_info[1])
    resp = {
        "id": thread_info[0],
        "forum": forum_info,
        "title": thread_info[2],
        "isClosed": true_false_ret(thread_info[3]),
        "user": user_info,
        "date": datetime.datetime.strftime(thread_info[5], "%Y-%m-%d %H:%M:%S"),
        "message": thread_info[6],
        "slug": thread_info[7],
        "isDeleted": true_false_ret(thread_info[8])
    }
    cursor.close()
    return jsonify(code=0, response=resp)


@thread_api.route('close/', methods=['POST'])
def thread_set_closed():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return open_close_thread(1, 1, thread_id)


@thread_api.route('open/', methods=['POST'])
def thread_set_opened():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return open_close_thread(0, 1, thread_id)


@thread_api.route('remove/', methods=['POST'])
def thread_set_deleted():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return open_close_thread(1, 0, thread_id)


@thread_api.route('restore/', methods=['POST'])
def thread_set_active():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return open_close_thread(0, 0, thread_id)


@thread_api.route('update/', methods=['POST'])
def thread_update():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'message' in req_json and 'slug' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    new_thread_msg = req_json['message']
    new_thread_slug = req_json['slug']

    sql_update = (new_thread_msg, new_thread_slug, thread_id)
    cursor.execute("UPDATE Thread SET message=%s, slug=%s WHERE id=%s", sql_update)
    conn.commit()
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    updated_thread = cursor.fetchall()
    resp = get_thread_info(updated_thread[0])
    return jsonify(code=0, responce=resp)


@thread_api.route('subscribe/', methods=['POST'])
def thread_subscribe():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    user_email = req_json['user']

    cursor.execute("SELECT * FROM Thread_Subscr WHERE thread=%s AND user=%s", (thread_id, user_email))
    if not cursor.fetchall():
        try:
            cursor.execute("INSERT INTO Thread_Subscr VALUES (%s,%s)", (user_email, thread_id))
            conn.commit()
        except Exception:
            return jsonify(code=3, response="Wrong request")

    resp = {
        "thread": thread_id,
        "user": user_email
    }
    return jsonify(code=0, response=resp)


@thread_api.route('unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    user_email = req_json['user']

    cursor.execute("SELECT * FROM Thread_Subscr WHERE thread=%s AND user=%s", (thread_id, user_email))
    if not cursor.fetchall():
        return jsonify(code=1, response="Subscription isn't found")

    cursor.execute("DELETE FROM Thread_Subscr WHERE thread=%s AND user=%s", (thread_id, user_email))
    conn.commit()

    resp = {
        "thread": thread_id,
        "user": user_email
    }
    return jsonify(code=0, response=resp)


@thread_api.route('list/', methods=['GET'])
def thread_list():
    conn = mysql.get_db()
    cursor = conn.cursor()

    forum_short_name = request.args.get('forum')
    user_email = request.args.get('user')
    if not (forum_short_name or user_email):
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
        first_part= "SELECT * FROM Thread WHERE forum='%s'" % forum_short_name
    else:
        first_part = "SELECT * FROM Thread WHERE user='%s'" % user_email
    second_part = " AND date >= '%s'" % since
    third_part = " ORDER BY date %s %s" % (order, limit)
    query = first_part + second_part + third_part
    try:
        cursor.execute(query)
    except Exception:
        return jsonify(code=3, response="Wrong request")

    all_threads = cursor.fetchall()
    end_list = []
    for x in all_threads:
        end_list.append(get_thread_info(x))
    return jsonify(code=0, response=end_list)


@thread_api.route('vote/', methods=['POST'])
def thread_vote():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'vote' in req_json):
        return jsonify(code=3, response="Wrong request")
    thread_id = req_json['thread']
    vote_value = req_json['vote']

    cursor.execute("SELECT likes, dislikes, points FROM Thread WHERE id='%s'" % thread_id)
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
    sql_update = (likes, dislikes, points, thread_id)
    cursor.execute("UPDATE Thread SET likes=%s, dislikes=%s, points=%s WHERE id=%s", sql_update)
    conn.commit()
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    updated_thread = cursor.fetchall()
    resp = get_thread_info(updated_thread[0])
    return jsonify(code=0, responce=resp)


@thread_api.route('listPosts/', methods=['GET'])
def thread_list_posts():
    conn = mysql.get_db()
    cursor = conn.cursor()

    thread_id = request.args.get('thread')
    if not thread_id:
        return jsonify(code=3, response="Wrong request")

    since = request.args.get('since')
    if not since:
        since = "1970-01-01"

    limit = 0
    if request.args.get('limit'):
        limit = int(request.args.get('limit'))

    order = request.args.get('order')
    if not order:
        order = "DESC"

    sort = request.args.get('sort')
    if sort == 'flat':
        resp = make_flat_sort(cursor, thread_id, since, limit, order)
    elif sort == 'tree':
        resp = make_tree_sort(cursor, thread_id, since, limit, order)
    return jsonify(code=0, responce=resp)


def make_flat_sort(cursor, thread_id, since, lim, order):
    limit = "LIMIT " + lim
    query_first = "SELECT P.id, P.date, P.thread, P.message, P.user, P.forum, P.parent, P.isApproved, P.isHighlighted, " \
                  "P.isEdited, P.isSpam, P.isDeleted, P.likes, P.dislikes, P.points, P.path FROM Post P " \
                  "INNER JOIN Thread T ON P.thread=T.id "
    query_second = "WHERE T.id=%s AND T.date >= %s ORDER BY T.date %s %s" % (thread_id, since, order, limit)
    full_query = query_first + query_second
    cursor.execute(full_query)
    posts_info = cursor.fetchall()
    end_list = []
    for x in posts_info:
        end_list.append(get_post_info_by_post(x))
    return end_list


def make_tree_sort(cursor, thread_id, since, limit, order):
    query_first = "SELECT P.id, P.date, P.thread, P.message, P.user, P.forum, P.parent, P.isApproved, P.isHighlighted, " \
                  "P.isEdited, P.isSpam, P.isDeleted, P.likes, P.dislikes, P.points, P.path FROM Post P " \
                  " INNER JOIN Thread T ON P.thread=T.id "
    query_second = " WHERE T.id=%s AND T.date >= %s ORDER BY P.path %s " % (thread_id, since, order)
    full_query = query_first + query_second
    cursor.execute(full_query)
    posts_info = cursor.fetchall()
    list_of_lists = []
    limit_list = []
    counter = 0
    for x in posts_info:
        limit_list.append(get_post_info_by_post(x))
        counter += 1
        if counter == limit:
            list_of_lists.append(list(limit_list))
            counter = 0
            del limit_list[:]
    list_of_lists.append(list(limit_list))
    return list_of_lists


# def get_post_info_by_post(post_info):
#     resp = {
#         "date": datetime.datetime.strftime(post_info[1], "%Y-%m-%d %H:%M:%S"),
#         "dislikes": post_info[13],
#         "forum": post_info[5],
#         "id": post_info[0],
#         "isApproved": true_false_ret(post_info[7]),
#         "isDeleted": true_false_ret(post_info[11]),
#         "isEdited": true_false_ret(post_info[9]),
#         "isHighlighted": true_false_ret(post_info[8]),
#         "isSpam": true_false_ret(post_info[10]),
#         "likes": post_info[12],
#         "message": post_info[3],
#         "parent": post_info[4],
#         "points": post_info[14],
#         "thread": post_info[2],
#         "user": post_info[4]
#     }
#     return resp


# def get_thread_info(thread):
#     thread_id = thread[0]
#     thread_forum = thread[1]
#     thread_title = thread[2]
#     thread_is_closed = thread[3]
#     thread_user = thread[4]
#     thread_date = datetime.datetime.strftime(thread[5], "%Y-%m-%d %H:%M:%S")
#     thread_msg = thread[6]
#     thread_slug = thread[7]
#     thread_is_del = thread[8]
#     thread_likes = thread[9]
#     thread_dislikes = thread[10]
#     thread_points = thread[11]
#
#     resp = {
#         "id": thread_id,
#         "forum": thread_forum,
#         "title": thread_title,
#         "isClosed": true_false_ret(thread_is_closed),
#         "user": thread_user,
#         "date": thread_date,
#         "message": thread_msg,
#         "slug": thread_slug,
#         "isDeleted": true_false_ret(thread_is_del),
#         "likes": thread_likes,
#         "dislikes": thread_dislikes,
#         "points": thread_points
#     }
#     return resp


def open_close_thread(is_closed, upd_or_open, thread_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    if not cursor.fetchall():
         return jsonify(code=1, response="Can't find this thread")
    action = "isDeleted"
    if upd_or_open:
        action = "isClosed"
    sql_data = (is_closed, thread_id)
    part1 = "UPDATE Thread SET %s=" % action
    part2 = "%s WHERE id=%s" % (is_closed, thread_id)
    query = part1 + part2
    cursor.execute(query)
    conn.commit()
    resp = {
        "thread": thread_id
    }
    cursor.close()
    return jsonify(code=0, response=resp)


# def get_thread_info_external(cursor, thread_id):
#     cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
#     thread = cursor.fetchall()
#     if not thread:
#         return {}
#     return get_thread_with_params(thread[0])

#
# def get_thread_with_params(thread):
#     thread_id = thread[0]
#     thread_forum = thread[1]
#     thread_title = thread[2]
#     thread_is_closed = thread[3]
#     thread_user = thread[4]
#     thread_date = datetime.datetime.strftime(thread[5], "%Y-%m-%d %H:%M:%S")
#     thread_msg = thread[6]
#     thread_slug = thread[7]
#     thread_is_del = thread[8]
#     thread_likes = thread[9]
#     thread_dislikes = thread[10]
#     thread_points = thread[11]
#
#     resp = {
#         "id": thread_id,
#         "forum": thread_forum,
#         "title": thread_title,
#         "isClosed": true_false_ret(thread_is_closed),
#         "user": thread_user,
#         "date": thread_date,
#         "message": thread_msg,
#         "slug": thread_slug,
#         "isDeleted": true_false_ret(thread_is_del),
#         "likes": thread_likes,
#         "dislikes": thread_dislikes,
#         "points": thread_points
#     }
#     return resp
#
#
# def true_false_ret(value):
#     if value == 0:
#         return False
#     return True
