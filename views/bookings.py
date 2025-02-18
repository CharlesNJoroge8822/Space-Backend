from flask import Blueprint, request, jsonify
from models import Booking, db

booking_bp = Blueprint("booking_bp", __name__)

# Create Booking
@booking_bp.route("/bookings", methods=['POST'])
def create_booking():
    data = request.get_json()

    user_id = data.get('user_id')
    space_id = data.get('space_id')
    date = data.get('date')

    new_booking = Booking(user_id=user_id, space_id=space_id, date=date)

    db.session.add(new_booking)
    db.session.commit()

    return jsonify({
        "id": new_booking.id,
        "user_id": new_booking.user_id,
        "space_id": new_booking.space_id,
        "date": new_booking.date
    }), 201

# Fetch Booking by ID
@booking_bp.route("/bookings/<int:id>", methods=['GET'])
def fetch_booking(id):
    booking = Booking.query.get(id)

    if booking is None:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({
        "id": booking.id,
        "user_id": booking.user_id,
        "space_id": booking.space_id,
        "date": booking.date
    })

# Update Booking
@booking_bp.route("/bookings/<int:id>", methods=['PATCH'])
def update_booking(id):
    booking = Booking.query.get(id)

    if booking is None:
        return jsonify({"error": "Booking not found"}), 404

    data = request.get_json()

    date = data.get('date')

    if date:
        booking.date = date

    db.session.commit()

    return jsonify({
        "id": booking.id,
        "user_id": booking.user_id,
        "space_id": booking.space_id,
        "date": booking.date
    }), 200

# Delete Booking
@booking_bp.route('/bookings/<int:id>', methods=['DELETE'])
def delete_booking(id):
    booking = Booking.query.get(id)

    if booking is None:
        return jsonify({"error": "Booking not found"}), 404

    db.session.delete(booking)
    db.session.commit()

    return jsonify({"msg": "Booking deleted successfully"}),200
