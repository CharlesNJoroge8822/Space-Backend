from flask import Flask, redirect, url_for, jsonify
from flask_migrate import Migrate
from models import db, User, Space, Booking, Payment, Agreement, TokenBlockList  
from flask_dance.contrib.google import make_google_blueprint, google
from flask_jwt_extended import JWTManager
from flask_cors import cross_origin, CORS

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ! Allow cross origins ..
CORS(app)

#! Google OAuth Setup
google_bp = make_google_blueprint(
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    redirect_to="google_login"
)
app.register_blueprint(google_bp, url_prefix="/google_login")

#! Google Login Route
@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    
    user_info = google.get("/oauth2/v2/userinfo").json()
    return jsonify(user_info)  #! Returns Google user details

#! Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "your_super_secret_key_here"


#! Initialize db and Migrate
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


#! Register Blueprints (Moved to Avoid Circular Imports)
from views.user_routes import user_bp
from views.space_routes import space_bp
from views.bookings import booking_bp
from views.payments_routes import payment_bp
from views.agreement_routes import agreement_bp
from views.auths import auth_bp

app.register_blueprint(user_bp)
app.register_blueprint(space_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(agreement_bp)
app.register_blueprint(auth_bp)




if __name__ == "__main__":
    app.run(debug=True)
