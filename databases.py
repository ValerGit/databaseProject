from flask import Flask, jsonify
from flaskext.mysql import MySQL
from flask import request
from werkzeug.exceptions import BadRequest

mysql = MySQL()

app = Flask(__name__)

base_path = '/db/api/'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'db_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)


def get_user_info(email):
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User where email=%s', email)
    return cursor.fetchall()


@app.route('/')
def hello_world():
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User')
    tag = cursor.fetchall()
    response = {
        "id": tag[0],
        "word": tag
    }
    return jsonify(code=0, response=response)


@app.route(base_path + 'user/create/', methods=['POST'])
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

    cursor.execute('INSERT INTO User VALUES (null,%s,%s,%s,%s,%s)', sql_data)
    conn.commit()

    resp = {
        "email": new_user_email,
        "username": new_user_username,
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": new_user_is_anon,
        "id": cursor.lastrowid,
    }
    return jsonify(code=0, response=resp)


@app.route(base_path + 'user/follow/', methods=['POST'])
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

    answ = (new_followee, new_follower)
    cursor.execute('INSERT INTO following VALUES (%s,%s)', answ)
    conn.commit()

    cursor.execute("SELECT follower FROM Following WHERE followee='%s'" % (new_followee))
    all_folwrs = cursor.fetchall()
    all_fetched = []
    for x in all_folwrs:
        all_fetched.append(x[0])

    cursor.execute("SELECT * FROM User where email='%s'" % (new_followee))
    usr_info = cursor.fetchall()
    one = ['one', 'two']

    resp = {
        "id": usr_info[0][0],
        "email": usr_info[0][1],
        "about": usr_info[0][2],
        "isAnonymous": usr_info[0][3],
        "name": usr_info[0][4],
        "username": usr_info[0][5],
        "followers": all_fetched
    }
    return jsonify(code=0, response=resp)


if __name__ == '__main__':
    app.run(debug=True)
