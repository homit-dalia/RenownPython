import os
from flask import Flask, request
import pymysql
import re

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main():
    if os.environ.get('GAE_ENV') == 'standard':
        unix_socket = f'/cloudsql/{db_connection_name}'
        cnx = pymysql.connect(user=db_user, password=db_password,unix_socket=unix_socket, db=db_name)
    else:
        host = '127.0.0.1'
        cnx = pymysql.connect(user=db_user, password=db_password,host=host, db=db_name)

    try:
        req_type = request.args["type"]
        print("Printing Request Type")
        print(req_type)
    except:
        return "Type of operation required. Please verify that the 'type' is in the URL."

    try:
        data = request.get_json()
        print("Printing Data")
        print(data)
    except:
        return "Missing data. Please verify that the data is in JSON format."
    

    def signup():
        try:
            username = data['username']
            mobile = data['mobile']
            email = data['email']
        except:
            return "Missing SignUp Values. Please verify that username, mobile, and email exists with the request."
        
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if not re.match(regex, email):
            return "Invalid email address. Please verify that the email is valid."
        
        try:
            with cnx.cursor() as cursor:
                cursor.execute(f"SELECT username FROM user WHERE username = '{username}';")

                if(cursor.rowcount > 0):
                    return "Username already exists. Please signup with a different username."

                cursor.execute(f"INSERT INTO user (username, mobile, email, fullname) VALUES ('{username}', '{mobile}', '{email}', '');")
                cnx.commit()
                return "User added successfully."
        except:
            return "Error adding new user."
        

    def login():
        pass

    def update():
        pass

    def display():
        try:
            arr = []
            with cnx.cursor() as cursor:
                cursor.execute('select * from user;')
                result = cursor.fetchall()
                for row in result:
                    arr.append(row)

        except:
            current_msg = 'No data found :('

    if req_type == "signup":
        return signup()
    elif req_type == "login":
        return login()
    elif req_type == "update":
        return update()
    elif req_type == "display":
        return display()
    
    cnx.close()

    return True


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
