from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Client")  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(200), nullable=True, default="default.jpg")

    bookings = db.relationship('Booking', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)
    agreements = db.relationship('Agreement', backref='user', lazy=True)
