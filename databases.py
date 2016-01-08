from flask import Flask, jsonify
from flaskext.mysql import MySQL
from user import user_api
from forum import forum_api
from threaad import thread_api

mysql = MySQL()

app = Flask(__name__)


app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'db_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

app.register_blueprint(user_api, url_prefix='/db/api/user/')
app.register_blueprint(forum_api, url_prefix='/db/api/forum/')
app.register_blueprint(thread_api, url_prefix='/db/api/thread/')

mysql.init_app(app)


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
