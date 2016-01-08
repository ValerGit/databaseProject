from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL

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

    if not ('name' in req_json and 'shortname' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_name = req_json['name']
    new_short_name = req_json['short_name']
    new_user = req_json['user']

    sql_data = (new_name, new_short_name, new_user)
    try:
        cursor.execute('INSERT INTO Forum VALUES Null,%s,%s,%s', sql_data)
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")
