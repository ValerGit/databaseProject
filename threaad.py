from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import datetime, time
from user import get_user_info_external
from forum import get_forum_info_external

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
    is_closed_fig = thread_info[3]
    user_info = thread_info[4]
    format_date = datetime.datetime.strftime(thread_info[5], "%Y-%m-%d %H:%M:%S")
    is_del_fig = thread_info[8]

    arg = request.args.get('related')
    if arg:

        if arg == 'user':
            user_info = get_user_info_external(cursor, thread_info[4])

        elif arg == 'forum':
            forum_info = get_forum_info_external(cursor, thread_info[1])

    is_closed = False
    if is_closed_fig:
        is_closed = True

    is_del = False
    if is_del_fig:
        is_del = True
    resp = {
        "id": thread_info[0],
        "forum": forum_info,
        "title": thread_info[2],
        "isClosed": is_closed,
        "user": user_info,
        "date": format_date,
        "message": thread_info[6],
        "slug": thread_info[7],
        "isDeleted": is_del
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

    try:
        cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    except Exception:
        return jsonify(code=3, response="Wrong request")
    thread = cursor.fetchall()
    if not thread:
        return jsonify(code=1, response="No such thread")
    thread_info = thread[0]

    sql_update = (new_thread_msg, new_thread_slug, thread_id)
    cursor.execute("UPDATE Thread SET message=%s, slug=%s WHERE id=%s", sql_update)
    conn.commit()

    forum_info = thread_info[1]
    title_info = thread_info[2]
    is_closed_fig = thread_info[3]
    user_info = thread_info[4]
    date_info = datetime.datetime.strftime(thread_info[5], "%Y-%m-%d %H:%M:%S")
    is_del_fig = thread_info[8]

    is_closed = False
    if is_closed_fig:
        is_closed = True

    is_del = False
    if is_del_fig:
        is_del = True

    resp = {
        "id": thread_id,
        "forum": forum_info,
        "title": title_info,
        "isClosed": is_closed,
        "user": user_info,
        "date": date_info,
        "message": new_thread_msg,
        "slug": new_thread_slug,
        "isDeleted": is_del
    }
    cursor.close()
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

    thr_date = datetime.datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(thr_date.timetuple())

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
    second_part = " AND date >= %s ORDER BY date %s %s" % (timestamp, order, limit)
    query = first_part + second_part
    try:
        cursor.execute(query)
    except Exception:
        return jsonify(code=3, response="Wrong request")
    all_threads = cursor.fetchall()
    end_list = []
    for x in all_threads:
        end_list.append(get_thread_info(x))
    return jsonify(code=0, response=end_list)


def get_thread_info(thread):
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

    is_closed = False
    if thread_is_closed:
        is_closed = True

    is_del = False
    if thread_is_del:
        is_del = True

    resp = {
        "id": thread_id,
        "forum": thread_forum,
        "title": thread_title,
        "isClosed": is_closed,
        "user": thread_user,
        "date": thread_date,
        "message": thread_msg,
        "slug": thread_slug,
        "isDeleted": is_del,
        "likes": thread_likes,
        "dislikes": thread_dislikes,
        "points": thread_points
    }
    return resp


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