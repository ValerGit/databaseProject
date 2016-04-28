from flask import Flask, jsonify
from flaskext.mysql import MySQL
from user import user_api
from forum import forum_api
from threaad import thread_api
from post import post_api

mysql = MySQL()

app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '12345678'
app.config['MYSQL_DATABASE_DB'] = 'db_project_small'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.register_blueprint(user_api, url_prefix='/db/api/user/')
app.register_blueprint(forum_api, url_prefix='/db/api/forum/')
app.register_blueprint(thread_api, url_prefix='/db/api/thread/')
app.register_blueprint(post_api, url_prefix='/db/api/post/')

mysql.init_app(app)


@app.route('/', methods=['GET'])
def hello():
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT @@FOREIGN_KEY_CHECKS')
    return jsonify(code=0, response=cursor.fetchall()[0][0])


@app.route('/db/api/status/', methods=['GET'])
def api_status():
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT count(id) FROM User')
    num_of_users = int(cursor.fetchall()[0][0])
    cursor.execute('SELECT count(id) FROM Thread')
    num_of_threads = int(cursor.fetchall()[0][0])
    cursor.execute('SELECT count(id) FROM Forum')
    num_of_forums = int(cursor.fetchall()[0][0])
    cursor.execute('SELECT count(id) FROM Post')
    num_of_posts = int(cursor.fetchall()[0][0])
    resp = {
        "user": num_of_users,
        "thread": num_of_threads,
        "forum": num_of_forums,
        "post": num_of_posts
    }
    return jsonify(code=0, response=resp)


@app.route('/db/api/clear/', methods=['POST'])
def api_clear():
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SET FOREIGN_KEY_CHECKS=0')
    conn.commit()
    cursor.execute('TRUNCATE TABLE User')
    conn.commit()
    cursor.execute('TRUNCATE TABLE Thread')
    conn.commit()
    cursor.execute('TRUNCATE TABLE Post')
    conn.commit()
    cursor.execute('TRUNCATE TABLE Forum')
    conn.commit()
    cursor.execute('TRUNCATE TABLE Following')
    conn.commit()
    cursor.execute('TRUNCATE TABLE Thread_Subscr')
    conn.commit()
    cursor.execute('SET FOREIGN_KEY_CHECKS=1')
    conn.commit()
    return jsonify(code=0, response="OK")


# if __name__ == '__main__':
#     app.run()
