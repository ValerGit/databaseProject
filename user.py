from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL
from utilities import true_false_ret, get_followees, get_followers, get_subscriptions, \
    zero_check, get_user_info_external
import datetime
import json


user_api = Blueprint('user_api', __name__)
mysql = MySQL()


@user_api.route('create/', methods=['POST'])
def user_create():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:

        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('username' in req_json and 'about' in req_json and 'name' in req_json and 'email' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_user_username = req_json['username']
    if new_user_username is None:
        new_user_username = ""
    new_user_about = req_json['about']
    new_user_name = req_json['name']
    if new_user_name is None:
        new_user_name = ""
    new_user_email = req_json['email']
    new_user_figure = 0

    if 'isAnonymous' in req_json:
        if req_json['isAnonymous'] is not False and req_json['isAnonymous'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_user_is_anon = req_json['isAnonymous']
        if not new_user_is_anon:
            new_user_figure = 0
        else:
            new_user_figure = 1
    else:
        new_user_is_anon = False

    sql_data = (new_user_email, new_user_about, new_user_figure, new_user_name, new_user_username)
    try:
        cursor.execute('INSERT INTO User VALUES (null,%s,%s,%s,%s,%s)', sql_data)
        conn.commit()
    except Exception:
        return jsonify(code=5, response='User already exist')

    resp = {
        "email": new_user_email,
        "username": new_user_username,
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": new_user_is_anon,
        "id": cursor.lastrowid,
    }
    return jsonify(code=0, response=resp)


@user_api.route('follow/', methods=['POST'])
def user_follow():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Can't parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_followee = req_json['followee']
    new_follower = req_json['follower']

    cursor.execute("SELECT * FROM Following WHERE followee = %s AND follower = %s", (new_followee, new_follower))
    if not cursor.fetchall():
        try:
            cursor.execute('INSERT INTO following VALUES (%s,%s)', (new_followee, new_follower))
            conn.commit()
        except Exception:
            return jsonify(code=3, response="Wrong request")

    return get_all_user_info(cursor, new_follower)


@user_api.route('unfollow/', methods=['POST'])
def user_unfollow():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong request")

    del_followee = req_json['followee']
    del_follower = req_json['follower']

    cursor.execute("DELETE FROM following WHERE followee=%s AND follower=%s", (del_followee, del_follower))
    conn.commit()
    return get_all_user_info(cursor, del_follower)


@user_api.route('updateProfile/', methods=['POST'])
def user_update():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('user' in req_json and 'about' in req_json and 'name' in req_json):
        return jsonify(code=3, response="Wrong request")

    user_email = req_json['user']
    upd_user_name = req_json['name']
    upd_user_about = req_json['about']

    upd_info = (upd_user_name, upd_user_about, user_email)
    try:
        cursor.execute("UPDATE User SET name=%s,about=%s WHERE email=%s", upd_info)
        conn.commit()
    except Exception:
        return jsonify(code=3, response="Wrong request")

    return get_all_user_info(cursor, user_email)


@user_api.route('details/', methods=['GET'])
def user_details():
    conn = mysql.get_db()
    cursor = conn.cursor()
    user_email = request.args.get('user')
    if not user_email:
        return jsonify(code=3, response="Wrong request")
    return get_all_user_info(cursor, user_email)


@user_api.route('listFollowers/', methods=['GET'])
def user_followers_list():
    conn = mysql.get_db()
    cursor = conn.cursor()
    user_email = request.args.get('user')
    if not user_email:
        return jsonify(code=3, response="Wrong request")

    limit = ''
    if request.args.get('limit'):
        limit = 'LIMIT '+request.args.get('limit')

    order = 'DESC'
    if request.args.get('order'):
        order=request.args.get('order')

    since_id = 1
    if request.args.get('since_id'):
        since_id=request.args.get('since_id')
    return list_folowings(cursor, limit, order, since_id, user_email, 1)


@user_api.route('listFollowing/', methods=['GET'])
def user_followings_list():
    conn = mysql.get_db()
    cursor = conn.cursor()

    user_email = request.args.get('user')
    if not user_email:
        return jsonify(code=3, response="Wrong request")

    limit = ''
    if request.args.get('limit',''):
        limit = 'LIMIT '+request.args.get('limit', '')

    order = 'DESC'
    if request.args.get('order', ''):
        order=request.args.get('order', '')

    since_id = 1
    if request.args.get('since_id', ''):
        since_id = request.args.get('since_id', '')

    return list_folowings(cursor, limit, order, since_id, user_email, 0)


@user_api.route('listPosts/', methods=['GET'])
def user_list_posts():
    conn = mysql.get_db()
    cursor = conn.cursor()
    user_email = request.args.get('user')
    if not user_email:
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
    query = "SELECT * FROM Post WHERE user='%s' AND date >= '%s' ORDER BY date %s %s" % (user_email, since, order, limit)
    cursor.execute(query)
    all_posts = cursor.fetchall()
    if not all_posts:
        return jsonify(code=0, response=[])
    end_list = []
    for x in all_posts:
        end_list.append(get_post_info(x))
    return jsonify(code=0, response=end_list)


def get_post_info(post_info):
    resp = {
        "date": datetime.datetime.strftime(post_info[1], "%Y-%m-%d %H:%M:%S"),
        "dislikes": post_info[13],
        "forum": post_info[5],
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
        "thread": post_info[2],
        "user": post_info[4]
    }
    return resp


def list_folowings(cursor, limit, order, since_id, user_email, is_follower):
    cursor.execute("SELECT * FROM User where email='%s'" % user_email)
    usr_info = cursor.fetchall()
    if not usr_info:
        return jsonify(code=1, response="No such list")
    if is_follower:
        query = "SELECT F.follower FROM Following F INNER JOIN User U ON F.follower = U.email"\
                " WHERE U.id >= %s AND F.followee= '%s' ORDER BY F.follower %s %s " % (since_id, user_email, order, limit)
        cursor.execute(query)
        all_followers = cursor.fetchall()
        all_fetched_followers = []
        # all = all_followers[0]
        for x in all_followers:
            all_fetched_followers.append(get_user_info_external(cursor, x))

    else:
        query = "SELECT F.followee FROM Following F INNER JOIN User U ON F.followee = U.email"\
                " WHERE U.id >= %s AND F.follower= '%s' ORDER BY F.followee %s %s " % (since_id, user_email, order, limit)
        cursor.execute(query)
        all_followers = cursor.fetchall()
        all_fetched_followers = []
        for x in all_followers:
            all_fetched_followers.append(get_user_info_external(cursor, x[0]))

    return jsonify(code=0, response=all_fetched_followers)


def get_all_user_info(cursor, user):
    cursor.execute("SELECT * FROM User where email='%s'" % user)
    usr_info = cursor.fetchall()
    if not usr_info:
        return jsonify(code=1, response="No such user")
    all_fetched_followers = get_followers(cursor, user)
    all_fetched_followees = get_followees(cursor, user)
    all_fetched_subscr = get_subscriptions(cursor, user)
    resp = {
        "id": usr_info[0][0],
        "email": usr_info[0][1],
        "about": usr_info[0][2],
        "isAnonymous": true_false_ret(usr_info[0][3]),
        "name": empty_check(usr_info[0][4]),
        "username": empty_check(usr_info[0][5]),
        "followers": all_fetched_followers,
        "following": all_fetched_followees,
        "subscriptions": all_fetched_subscr
    }
    return jsonify(code=0, response=resp)


def empty_check(value):
    if value == "":
        return None
    return value
