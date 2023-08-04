import os
from flask import Flask, request
import pymysql
import requests

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main():
    try:
        data = request.get_json()
        print(data)
    except:
        pass
    # When deployed to App Engine, the `GAE_ENV` environment variable will be
    # set to `standard`
    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the local socket interface for accessing Cloud SQL
        unix_socket = f'/cloudsql/{db_connection_name}'
        cnx = pymysql.connect(user=db_user, password=db_password,unix_socket=unix_socket, db=db_name)
    else:
        # If running locally, use the TCP connections instead
        # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
        # so that your application can use 127.0.0.1:3306 to connect to your
        # Cloud SQL instance
        host = '127.0.0.1'
        cnx = pymysql.connect(user=db_user, password=db_password,host=host, db=db_name)

    try:
        arr = []
        with cnx.cursor() as cursor:
            cursor.execute('select * from user;')
            result = cursor.fetchall()
            for row in result:
                arr.append(row)
        cnx.close()
    except:
        current_msg = 'No data found :('

    return arr
# [END gae_python37_cloudsql_mysql]


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
