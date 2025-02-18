from datetime import datetime
from app import db

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)

    payment = db.relationship('Payment', backref='booking', uselist=False)

    @staticmethod
    def is_space_available(space_id, start_time, end_time):
        existing_booking = Booking.query.filter(
            Booking.space_id == space_id,
            Booking.status == "Confirmed",  
            Booking.end_time > start_time  
        ).first()
        return existing_booking is None
