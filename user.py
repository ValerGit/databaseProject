from werkzeug.exceptions import BadRequest
from flask import jsonify, Blueprint, request
from flaskext.mysql import MySQL

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
    new_user_about = req_json['about']
    new_user_name = req_json['name']
    new_user_email = req_json['email']
    new_user_figure = 0

    if 'isAnonymous' in req_json:
        if req_json['isAnonymous'] is not False and req_json['isAnonymous'] is not True:
            return jsonify(code=3, response="Wrong parameters")

        new_user_is_anon = req_json['isAnonymous']
        if req_json['isAnonymous'] is False:
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
        return jsonify(code=5, responce='user already exist')

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
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong request")

    new_followee = req_json['followee']
    new_follower = req_json['follower']

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

    cursor.execute("DELETE FROM following WHERE followee=%s and follower=%s", (del_followee, del_follower))
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
    try:
        user_email = request.args.get('user','')
    except KeyError:
        return jsonify(code=3, response="Wrong request")
    return get_all_user_info(cursor, user_email)


@user_api.route('listFollowers/', methods=['GET'])
def user_followers_list():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        user_email = request.args.get('user', '')
    except KeyError:
        return jsonify(code=3, response="Wrong request")

    limit=''
    if request.args.get('limit',''):
        limit = 'LIMIT '+request.args.get('limit', '')

    order='DESC'
    if request.args.get('order', ''):
        order=request.args.get('order', '')

    since_id = 1
    if request.args.get('since_id', ''):
        since_id=request.args.get('since_id', '')
    return list_folowings(cursor, limit, order, since_id, user_email, 1)


@user_api.route('listFollowing/', methods=['GET'])
def user_followings_list():
    conn = mysql.get_db()
    cursor = conn.cursor()
    try:
        user_email = request.args.get('user', '')
    except KeyError:
        return jsonify(code=3, response="Wrong request")

    limit = ''
    if request.args.get('limit',''):
        limit = 'LIMIT '+request.args.get('limit', '')

    order='DESC'
    if request.args.get('order', ''):
        order=request.args.get('order', '')

    since_id=1
    if request.args.get('since_id', ''):
        since_id = request.args.get('since_id', '')

    return list_folowings(cursor, limit, order, since_id, user_email, 0)


def list_folowings(cursor, limit, order, since_id, user_email, is_follower):
    cursor.execute("SELECT * FROM User where email='%s'" % user_email)
    usr_info = cursor.fetchall()
    if usr_info:
        if is_follower:
            first = '''SELECT F.follower FROM Following F INNER JOIN User U ON F.follower = U.email
                          WHERE U.id >= %s AND F.followee= '%s' ''' % (since_id, user_email)
            second = " ORDER BY F.follower %s %s" % (order, limit)
            query = first + second
            cursor.execute(query)
            all_followers = cursor.fetchall()
            all_fetched_followers = []
            for x in all_followers:
                all_fetched_followers.append(x[0])
            all_fetched_followees = get_followees(cursor, user_email)
        else:
            first = '''SELECT F.followee FROM Following F INNER JOIN User U ON F.followee = U.email
                          WHERE U.id >= %s AND F.follower= '%s' ''' % (since_id, user_email)
            second = " ORDER BY F.followee %s %s" % (order, limit)
            query = first + second
            cursor.execute(query)
            all_followers = cursor.fetchall()
            all_fetched_followees = []
            for x in all_followers:
                all_fetched_followees.append(x[0])
            all_fetched_followers = get_followers(cursor, user_email)

        if usr_info[0][3]:
            anon = True
        else:
            anon = False
        resp = {
            "id": usr_info[0][0],
            "email": usr_info[0][1],
            "about": usr_info[0][2],
            "isAnonymous": anon,
            "name": usr_info[0][4],
            "username": usr_info[0][5],
            "followers": all_fetched_followers,
            "following": all_fetched_followees
        }
        return jsonify(code=0, response=resp)
    return jsonify(code=1, response="User doesn't exist")


def get_all_user_info(cursor, user):
    cursor.execute("SELECT * FROM User where email='%s'" % user)
    usr_info = cursor.fetchall()
    if usr_info:
        all_fetched_followers = get_followers(cursor, user)
        all_fetched_followees = get_followees(cursor, user)
        if usr_info[0][3]:
            anon = True
        else:
            anon = False
        resp = {
            "id": usr_info[0][0],
            "email": usr_info[0][1],
            "about": usr_info[0][2],
            "isAnonymous": anon,
            "name": usr_info[0][4],
            "username": usr_info[0][5],
            "followers": all_fetched_followers,
            "following": all_fetched_followees
        }
        return jsonify(code=0, response=resp)
    return jsonify(code=1, response="User doesn't exist")


def get_followers(cursor, followee):
    cursor.execute("SELECT follower FROM Following WHERE followee='%s'" % followee)
    all_folwrs = cursor.fetchall()
    all_fetched_followers = []
    for x in all_folwrs:
        all_fetched_followers.append(x[0])
    return all_fetched_followers


def get_followees(cursor, follower):
    cursor.execute("SELECT followee FROM Following WHERE follower='%s'" % follower)
    all_folwees = cursor.fetchall()
    all_fetched_followees = []
    for x in all_folwees:
        all_fetched_followees.append(x[0])
    return all_fetched_followees


def get_user_info_external(cursor, user):
    cursor.execute("SELECT * FROM User where email='%s'" % user)
    usr_info = cursor.fetchall()
    resp = {}
    if usr_info:
        all_fetched_followers = get_followers(cursor, user)
        all_fetched_followees = get_followees(cursor, user)
        if usr_info[0][3]:
            anon = True
        else:
            anon = False
        resp = {
            "id": usr_info[0][0],
            "email": usr_info[0][1],
            "about": usr_info[0][2],
            "isAnonymous": anon,
            "name": usr_info[0][4],
            "username": usr_info[0][5],
            "followers": all_fetched_followers,
            "following": all_fetched_followees
        }
    return resp
