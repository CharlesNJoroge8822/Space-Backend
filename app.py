from flask import Flask
from flask_migrate import Migrate
from models import db, User, Space, Booking, Payment, Agreement, TokenBlockList  # ✅ Ensure correct import

app = Flask(__name__)

# ✅ Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Initialize db and Migrate
db.init_app(app)
migrate = Migrate(app, db)

# ✅ Register Blueprints (Moved to Avoid Circular Imports)
from views.user_routes import user_bp
from views.space_routes import space_bp
from views.bookings import booking_bp
from views.payments_routes import payment_bp
from views.agreement_routes import agreement_bp

app.register_blueprint(user_bp)
app.register_blueprint(space_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(agreement_bp)



if __name__ == "__main__":
    app.run(debug=True)
