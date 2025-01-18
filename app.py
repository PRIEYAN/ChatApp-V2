from flask import Flask, url_for, redirect, request, render_template, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import datetime
from flask_cors import CORS

app = Flask(__name__)
oauth = OAuth(app)
socketio = SocketIO(app)
app.secret_key = 'lkinllvwkgg3wo2p'

# Enable CORS (Cross-Origin Resource Sharing)
CORS(app)

# Database connection
client = MongoClient('mongodb://localhost:27018/')
db = client.mydatabase
users = db['users']
rooms = db["rooms"]
messages_collection = db["messages"]

# Google OAuth setup
google = oauth.register(
    name='google',
    client_id='clientid',
    client_secret='clientsecret',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

# Home route
@app.route('/')
def home():
    if not session.get('auth'):
        return render_template('index.html')
    return redirect('/dashboard')

# Login route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = users.find_one({"email": email})
        if existing_user and check_password_hash(existing_user['password'], password):
            session['email'] = email
            session['username'] = existing_user['username']
            session['auth'] = True
            return redirect('/dashboard')

        message = "*Invalid Email or Password"
        return render_template('login.html', message=message)
    
    return render_template('login.html')

# Sign-up route
@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if users.find_one({'email': email}) or users.find_one({'username': username}):
            message = "*User already exists"
            return render_template('signin.html', message=message)

        hashed_password = generate_password_hash(password)
        users.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })

        session['username'] = username
        session['email'] = email
        session['auth'] = True
        return redirect('/dashboard')
    
    return render_template("signin.html")

# Google login route
@app.route('/google')
def google_login():
    redirect_uri = url_for("authorize_google", _external=True)
    return google.authorize_redirect(redirect_uri)

# Google authorization route
@app.route("/authorize/google")
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()
    email = user_info.get("email")

    if not users.find_one({"email": email}):
        users.insert_one({
            "username": user_info.get("given_name"),
            "email": email,
            "password": None
        })

    session['auth'] = True
    session['email'] = email
    session['username'] = user_info.get("given_name")
    return redirect('/dashboard')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if not session.get('auth'):
        return redirect('/login')

    user_rooms = list(rooms.find({"creater": session['email']}))
    return render_template(
        'dashboard.html',
        username=session['username'],
        email=session['email'],
        creation_date=datetime.datetime(2025, 1, 15).strftime('%B %d, %Y'),
        rooms=user_rooms
    )

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

# Room creation route
@app.route('/room', methods=['POST'])
def create_room():
    if not session.get('auth'):
        return redirect('/login')

    roomname = request.form.get('roomname')

    existing_room = rooms.find_one({"roomname": roomname, "creater": session['email']})
    if existing_room:
        return redirect('/dashboard')

    room = {
        "creater": session['email'],
        "roomname": roomname,
        "created_at": datetime.datetime.utcnow()
    }
    rooms.insert_one(room)
    return redirect('/dashboard')

# Room viewing route
@app.route('/room/<roomname>')
def room(roomname):
    if not session.get('auth'):
        return redirect('/login')
    room_data = rooms.find_one({"roomname": roomname})
    if not room_data:
        return redirect('/dashboard')
    room_messages = messages_collection.find({"roomname": roomname}).sort("timestamp", 1)

    return render_template('app.html', roomname=room_data['roomname'], room_data=room_data, room_messages=room_messages)

# SocketIO event for joining a room
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)

# SocketIO event for sending a message
@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = session.get('username')
    message_data = {
        "roomname": room,
        "username": username,
        "message": message,
        "timestamp": datetime.datetime.utcnow()
    }
    messages_collection.insert_one(message_data)
    emit('receive_message', {'username': username, 'message': message}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
