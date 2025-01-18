from flask import Flask, url_for, redirect, request, render_template, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.secret_key = 'lkinllvwkgg3wo2p'  

# Database connection
client = MongoClient('mongodb://localhost:27018/')
db = client.mydatabase
users = db['users']

@app.route('/')
def home():
    if not session.get('auth'):
        return render_template('index.html')
    else:
        return redirect('dashboard')

# Login route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        existing_email = users.find_one({"email": email})

        if existing_email and check_password_hash(existing_email['password'], password):
            session['email'] = email
            session['username'] = existing_email['username']
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

        existing_name = users.find_one({'username': username})
        existing_email = users.find_one({'email': email})

        if existing_email or existing_name:
            message = "*User already exists"
            return render_template('signin.html', message=message)

        hashed_password = generate_password_hash(password)
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password
        }
        users.insert_one(new_user)

        session['username'] = username
        session['email'] = email
        session['auth'] = True
        return redirect('/dashboard')
    
    return render_template("signin.html")

# app
@app.route('/dashboard')
def dashboard():
    session['creation_date'] = datetime.datetime(2025, 1, 15).strftime('%B %d, %Y')
    if not session.get('auth'):
        return redirect('/login')  
    return render_template(
        'dashboard.html',
        username=session['username'],
        email=session['email'],
        creation_date=session['creation_date']
    )

# Logout route
@app.route('/logout',methods=['POST','GET'])
def logout():
    session.clear()  
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
