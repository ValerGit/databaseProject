from flask import Flask, jsonify
from flaskext.mysql import MySQL
from flask import request

mysql = MySQL()

app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'test'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

# @app.route('/', methods=['GET', 'POST'])
@app.route('/')
def hello_world():
    conn = mysql.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ask_tag')
    tag = cursor.fetchone()
    response = {
        "id": tag[0],
        "word": tag[1]
    }
    return jsonify(code=0, response=response)


if __name__ == '__main__':
    app.run()
