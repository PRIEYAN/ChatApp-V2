# config.py

from flask import Flask
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth
from pymongo import MongoClient
from flask_cors import CORS
import datetime

# Initialize Flask extensions
socketio = SocketIO()
oauth = OAuth()
client = MongoClient('mongodb://localhost:27018/')
db = client.mydatabase
users = db['users']
rooms = db["rooms"]
messages_collection = db["messages"]

def create_app():
    app = Flask(__name__)
    app.secret_key = 'lkinllvwkgg3wo2p'
    
    # Enable CORS (Cross-Origin Resource Sharing)
    CORS(app)

    # Setup OAuth
    oauth.init_app(app)
    
    # Setup SocketIO
    socketio.init_app(app)

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

    # Return the app instance
    return app, google
