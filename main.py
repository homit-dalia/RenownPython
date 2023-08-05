import os
from flask import Flask, request
import pymysql
import re
import jwt
import datetime
import random
from twilio.rest import Client

app = Flask(__name__)

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
app.config['SECRET_KEY'] = str(os.environ.get('SECRET_KEY'))

twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

if os.environ.get('GAE_ENV') == 'standard':
    unix_socket = f'/cloudsql/{db_connection_name}'
    cnx = pymysql.connect(user=db_user, password=db_password,unix_socket=unix_socket, db=db_name)
else:
    host = '127.0.0.1/5000'
    cnx = pymysql.connect(user=db_user, password=db_password,host=host, db=db_name)

def get_data():
    try:
        data = request.get_json()
        return data
    except:
        return False

def send_otp(mobile):
    try:
        password = random.randint(100000, 999999)
        client = Client(twilio_account_sid, twilio_auth_token)
        client.messages.create(
            body=f"Your OTP is {password}",
            from_='+17756180651',
            to=f'+91{mobile}'
        )
        return password
    except Exception as e:
        return f"Error sending OTP - {e}"  

@app.route('/', methods=['GET','POST'])
def main():
    return "Welcome to Renown Backend Assignment. Please verify that the route is either signup, login, update or display."

@app.route('/signup', methods=['POST'])
def signup():
    data = get_data()
    if(not data):
        return "No data sent with the request."
    try:
        username = data['username']
        mobile = data['mobile']
        email = data['email']
    except:
        return "Missing SignUp Values. Please verify that username, mobile, and email are sent with the request."
    
    if(len(username) < 4 or len(username) > 20):
        return "Invalid username. Please enter a username that contains 4 - 20 characters."
    
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if not re.match(email_regex, email):
        return "Invalid email address. Please verify that the email is valid."
    
    if(len(mobile) != 10):
        return "Invalid mobile number. Please verify that the mobile number is valid."
    
    try:
        with cnx.cursor() as cursor:
            cursor.execute(f"SELECT username FROM users WHERE username = '{username}';")

            if(cursor.rowcount > 0):
                return "Username already exists. Please signup with a different username."

            cursor.execute(f"INSERT INTO users (username, mobile, email, fullname, password) VALUES ('{username}', '{mobile}', '{email}', '', -1);")
            password = send_otp(mobile)
            cursor.execute(f"UPDATE users SET password = '{password}' WHERE username = '{username}';")
            cnx.commit()
            return "User added successfully."
    except Exception as e:
        return f"Error adding new user - {e}"
      
@app.route('/login', methods=['POST'])
def login():
    data = get_data()
    if(not data):
        return "No data sent with the request."
    cursor = cnx.cursor()
    try:
        username = data.get('username', None)
        if username is None:
            return "Missing Login Values. Please verify that username exists with the request."

        user = []
        mobile = ""

        cursor.execute(f"SELECT * FROM users WHERE username = '{username}';")
        result = cursor.fetchone()

        if(cursor.rowcount == 0):
            return "Username does not exist. Please signup first."

        for row in result:
            user.append(row)
        mobile = user[2]
        
        resend = data.get('resend', None)
        if (resend == "True"):
            try:
                cursor.execute(f"SELECT mobile FROM users WHERE username = '{username}';")
                password = send_otp(mobile)
                cursor.execute(f"UPDATE users SET password = '{password}' WHERE username = '{username}';")
                cnx.commit()
                return f"OTP sent to your number ending with ******{user[2][-4:]}"
            except Exception as e:
                return f"Error sending or storing OTP - {e}"

        otp = data.get('otp', None)
        if otp is None or otp == -1:
            return "Missing OTP Value. Please verify that otp exists with the request."
        
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}';")
        result = cursor.fetchone()
        

        user = []
        for row in result:
            user.append(row)
        password = user[5]

        if(otp != str(password)):
            return "Invalid OTP. Please renter OTP."
        
        token = jwt.encode(payload={"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, key=app.config['SECRET_KEY'], algorithm='HS256')
        return str(token)
        
    except Exception as e:
        return f"Error Logging in - {e}"
        
@app.route('/update', methods=['POST'])
def update():
    data = get_data()
    if(not data):
        return "No data sent with the request."
    try:
        token = data.get('token', None)
        if token is None:
            return "Missing Token."
        token_data = jwt.decode(jwt=token, key=app.config['SECRET_KEY'], algorithms=["HS256"])
        username = token_data.get('username', None)
        if username is None:
            return "Missing Username with Token."
        
        fullname = data.get('fullname', None)
        if(fullname is None or len(fullname) < 3):
            return "Invalid fullname. Please enter a fullname that contains at least 3 characters."

        with cnx.cursor() as cursor:
            cursor.execute(f"UPDATE users SET fullname = '{fullname}' WHERE username = '{username}';")
            cursor.execute(f"UPDATE users SET password = -1 WHERE username = '{username}';")
            cnx.commit()
            return "User updated successfully"
        
    except Exception as e:
        return f"Error Updating user - {e}"

@app.route('/display', methods=['GET'])
def display():
    try:
        resp = {}
        resp['count'] = 0
        resp['users'] = []
        arr = []
        with cnx.cursor() as cursor:
            cursor.execute('select * from users;')
            result = cursor.fetchall()
            for row in result:
                arr.append(row[0:5])
        resp['count'] = len(arr)
        resp['users'] = arr
        return resp
    except Exception as e:
        return f'No data found :(. {e}'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
