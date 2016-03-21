from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import datetime
from utilities import get_user_info_external, get_forum_info_external, \
    true_false_ret, get_thread_info, flat_sort, get_post_info_special, tree_sort, \
    count_posts_in_thread,special_tree_sort

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
    if not request.args.get('thread'):
        return jsonify(code=3, response="Wrong request")

    thread_id = request.args.get('thread')
    try:
        cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    except Exception:
        return jsonify(code=3, response="Wrong request")

    thread = cursor.fetchall()
    if not thread:
        return jsonify(code=3, response="No such thread")
    thread_info = thread[0]

    forum_info = thread_info[1]
    user_info = thread_info[4]
    related_list = request.args.getlist('related')

    for related in related_list:
        if related == 'user':
            user_info = get_user_info_external(cursor, thread_info[4])
        elif related == 'forum':
            forum_info = get_forum_info_external(cursor, thread_info[1])
        elif related == 'thread':
            return jsonify(code=3, response="Wrong request")

    num_posts = count_posts_in_thread(cursor, thread_id)
    if true_false_ret(thread_info[8]):
        num_posts = 0

    resp = {
        "id": thread_info[0],
        "forum": forum_info,
        "title": thread_info[2],
        "isClosed": true_false_ret(thread_info[3]),
        "user": user_info,
        "date": datetime.datetime.strftime(thread_info[5], "%Y-%m-%d %H:%M:%S"),
        "message": thread_info[6],
        "slug": thread_info[7],
        "isDeleted": true_false_ret(thread_info[8]),
        "likes": thread_info[9],
        "dislikes": thread_info[10],
        "points": thread_info[11],
        "posts": num_posts
    }
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
    return open_close(1, thread_id)


@thread_api.route('open/', methods=['POST'])
def thread_set_opened():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return open_close(0, thread_id)


@thread_api.route('remove/', methods=['POST'])
def thread_set_deleted():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return rem_restore(1, thread_id)


@thread_api.route('restore/', methods=['POST'])
def thread_set_active():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong request")

    thread_id = req_json['thread']
    return rem_restore(0, thread_id)


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
    resp = get_thread_info(cursor, updated_thread[0])
    return jsonify(code=0, response=resp)


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
        first_part = "SELECT * FROM Thread WHERE forum='%s'" % forum_short_name
    else:
        first_part = "SELECT * FROM Thread WHERE user='%s'" % user_email
    second_part = " AND date >= '%s' ORDER BY date %s %s" % (since, order, limit)
    query = first_part + second_part
    try:
        cursor.execute(query)
    except Exception:
        return jsonify(code=3, response="Wrong request")
    all_threads = cursor.fetchall()
    if not all_threads:
        return jsonify(code=0, response=[])
    end_list = []
    for x in all_threads:
        end_list.append(get_thread_info(cursor, x))
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
    resp = get_thread_info(cursor, updated_thread[0])
    return jsonify(code=0, response=resp)


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

    order_req = request.args.get('order')
    order = "DESC"
    if order_req == "asc":
        order = "ASC"

    sort = request.args.get('sort')
    resp = []
    if sort:

        if sort == 'flat':
            resp = make_flat_sort_thread(cursor, thread_id, since, limit, order)
        elif sort == 'tree':
            resp = make_tree_sort_thread(cursor, thread_id, since, limit, order)
        elif sort == 'parent_tree':
            resp = make_parent_tree_sort_thread(cursor, thread_id, since, limit, order)
    else:
        lim = ""
        if limit != 0:
            lim = "LIMIT " + str(limit)

        full_query = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
                     "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
                     "FROM Post WHERE thread=%s AND date >= '%s' " \
                     "ORDER BY date %s %s" % (thread_id, since, order, lim)
        cursor.execute(full_query)
        posts_info = cursor.fetchall()
        if posts_info:
            resp = flat_sort(cursor, posts_info)
        else:
            return jsonify(code=0, response={})

    return jsonify(code=0, response=resp)


def make_flat_sort_thread(cursor, thread_id, since, limit, order):
    lim = ""
    if limit != 0:
        lim = "LIMIT " + str(limit)
    full_query = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
                 "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
                 "FROM Post WHERE thread=%s AND date >= '%s' " \
                 "ORDER BY date %s %s" % (thread_id, since, order, lim)
    cursor.execute(full_query)
    posts_info = cursor.fetchall()
    return flat_sort(cursor, posts_info)


def make_tree_sort_thread(cursor, thread_id, since, limit, order):
    lim = ""
    if limit != 0:
        lim = "LIMIT " + str(limit)
    if order == 'DESC':
        special = "%.%"
        first = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
            "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
            "FROM Post WHERE thread=%s AND date >= '%s' AND path not like '%s' " \
            "ORDER BY path DESC %s" % (thread_id, since, special, lim)
        cursor.execute(first)
        posts_info = cursor.fetchall()
        second = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
            "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
            "FROM Post WHERE thread=%s AND date >= '%s' AND path LIKE '%s' " \
            "ORDER BY substring_index(path, '.', 2) desc,  path ASC %s" % (thread_id, since, special, lim)
        cursor.execute(second)
        childs_info = cursor.fetchall()
        return special_tree_sort(posts_info, childs_info, limit)

    else:
        full_query = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
            "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
            "FROM Post WHERE thread=%s AND date >= '%s' ORDER BY path ASC %s" % (thread_id, since, lim)
        cursor.execute(full_query)
        posts_info = cursor.fetchall()
        return tree_sort(posts_info, lim)


def make_parent_tree_sort_thread(cursor, thread_id, since, limit, order):
    if order == 'DESC':
        sec = "ORDER BY substring_index(path, '.', 1) DESC, path ASC "
    else:
        sec = "ORDER BY path ASC"

    first = "SELECT id, date, thread, message, user, forum, parent, isApproved, " \
            "isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path " \
            "FROM Post P WHERE thread=%s AND date >= '%s' " % (thread_id, since)

    full_query = first + sec
    cursor.execute(full_query)
    posts_info = cursor.fetchall()
    limit_list = []
    counter = 0
    for x in posts_info:
        if '.' not in x[15]:
            counter += 1
        if counter > limit:
            return limit_list
        limit_list.append(get_post_info_special(x))
    return limit_list


def rem_restore(is_closed, thread_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    if not cursor.fetchall():
        return jsonify(code=1, response="Can't find this thread")
    query = "UPDATE Thread SET isDeleted=%s WHERE id=%s" % (is_closed, thread_id)
    cursor.execute(query)
    conn.commit()
    del_posts = "UPDATE Post SET isDeleted=%s WHERE thread=%s" % (is_closed, thread_id)
    cursor.execute(del_posts)
    conn.commit()
    resp = {
        "thread": thread_id
    }
    cursor.close()
    return jsonify(code=0, response=resp)


def open_close(is_closed, thread_id):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    if not cursor.fetchall():
        return jsonify(code=1, response="Can't find this thread")
    query = "UPDATE Thread SET isClosed=%s WHERE id=%s" % (is_closed, thread_id)
    cursor.execute(query)
    conn.commit()
    resp = {
        "thread": thread_id
    }
    cursor.close()
    return jsonify(code=0, response=resp)