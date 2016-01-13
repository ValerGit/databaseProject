from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
import re

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
    if 'parent' in req_json:
        new_post_parent_id = req_json['parent']
    new_post_path = get_post_path(cursor, new_post_parent_id)
    sql_data = (new_post_date, new_post_thread_id, new_post_message, new_post_user_email, new_post_forum_short_name,
                new_post_parent_id, new_post_is_approved, new_post_is_high, new_post_is_edited, new_post_is_spam,
                new_post_is_del, new_post_path)
    cursor.execute("INSERT INTO Post VALUES (null,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,%s)", sql_data)
    conn.commit()
    return jsonify(resp = 0)


def get_post_path(cursor, new_post_parent_id):
    if new_post_parent_id:
        cursor.execute("SELECT path FROM Post WHERE id='%s'" % new_post_parent_id)
        parent_path = cursor.fetchall()[0][0]
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
        new_post_parent_id = 0
        cursor.execute("SELECT max(path) FROM Post WHERE path LIKE '______'")
        biggest_post = cursor.fetchall()[0][0]
        if biggest_post is not None:
            post = biggest_post[0]
            biggest_post_id = int(biggest_post) + 1
            new_post_path = '{0:06d}'.format(biggest_post_id)
        else:
            new_post_path = '{0:06d}'.format(1)
    return new_post_path