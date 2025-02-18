from datetime import datetime
from app import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Processing")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    mpesa_transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)

    def __init__(self, booking_id, user_id, amount, mpesa_transaction_id, phone_number):
        self.booking_id = booking_id
        self.user_id = user_id
        self.amount = amount
        self.mpesa_transaction_id = mpesa_transaction_id
        self.phone_number = phone_number
