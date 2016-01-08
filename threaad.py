from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import datetime
from time import mktime

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
    new_thread_is_del_figure = 0

    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_thread_is_del = req_json['isDeleted']

        if req_json['isDeleted'] is True:
            new_thread_is_del_figure = 1
    else:
        new_thread_is_del = False

    new_thread_is_closed_figure = 0
    if new_thread_is_closed:
        new_thread_is_closed_figure = 1
    sql_data = (new_thread_forum, new_thread_title, new_thread_is_closed_figure, new_thread_user, new_thread_date,
                new_thread_msg, new_thread_slug, new_thread_is_del_figure, 0, 0, 0)

    thr_date = datetime.datetime.strptime(new_thread_date, "%Y-%m-%d %H:%M:%S")
    timestamp = mktime(thr_date.timetuple())

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
    return jsonify(code=0, response=resp)
