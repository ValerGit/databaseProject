from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
from user import get_user_info_external

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
