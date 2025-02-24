import os
import pathlib
import random
import string
from flask import Flask, redirect, url_for, jsonify, request, session
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from models import db, User, Space, Booking, Payment, Agreement, TokenBlockList  
from google_auth_oauthlib.flow import Flow
from flask_dance.contrib.google import make_google_blueprint, google                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from googleapiclient.discovery import build
from dotenv import load_dotenv

app = Flask(__name__)

CORS(app)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Function to generate random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    random_password = ''.join(random.choice(characters) for i in range(length))
    return random_password

# Google OAuth Setup with Flow
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, ".env")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/google_login/callback"
)

# Route to Initiate Google OAuth
@app.route("/authorize_google")
def authorize_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/google_login/callback")
def google_callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Store credentials in the session
    session['credentials'] = credentials_to_dict(credentials)

    # Fetch user info from Google API
    user_info = get_user_info(credentials)

#! Google Login Route                                                                                                                                                                                                                                                                                                                                           
@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    
    # Check if user exists or create a new user
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Generate random password and hash it
        random_password = generate_random_password()
        hashed_password = generate_password_hash(random_password)

        # Create a new user with the hashed password
        user = User(
            name=user_info['name'], 
            email=user_info['email'], 
            password=hashed_password  # Storing hashed password
        )
        db.session.add(user)
        db.session.commit()

    # Store user info in session and redirect to the spaces page
    session['user_info'] = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role  # Assuming your User model has a 'role' field
    }

    # Redirect to the frontend with user data
    return redirect(f"http://localhost:5173/profile?user_id={user.id}&name={user.name}&email={user.email}&role={user.role}")

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_user_info(credentials):
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture']
    }

# Database Configuration

@app.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    print("Received Callback:", data)  # Debugging
    return jsonify({"message": "Callback received"}), 200

#! Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey")



# Initialize db and Migrate
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Register Blueprints
from views.user_routes import user_bp
from views.space_routes import space_bp
from views.bookings import booking_bp
from views.payments_routes import payment_bp
from views.agreement_routes import agreement_bp
# from views.auth import auth_bp

app.register_blueprint(user_bp)
app.register_blueprint(space_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(agreement_bp)
# app.register_blueprint(auth_bp)

if __name__ == "_main_":
    app.run(debug=True)