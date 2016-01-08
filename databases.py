from flask import Flask, jsonify, Blueprint, request
from flaskext.mysql import MySQL

from user import user_api
from forum import forum_api

mysql = MySQL()

app = Flask(__name__)


app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'db_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'


app.register_blueprint(user_api, url_prefix='/db/api/user/')
app.register_blueprint(forum_api, url_prefix='/db/api/forum/')

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

if __name__ == '__main__':
    app.run(debug=True)
