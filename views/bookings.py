from flask import Blueprint, request, jsonify
from models import Booking, db, Space, User
from datetime import datetime
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity

booking_bp = Blueprint("booking_bp", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

#! CREATE BOOKING (Starts as "Pending Payment")
@booking_bp.route("/bookings", methods=['POST'])
def create_booking():
    try:
        data = request.get_json()

        required_fields = ["user_id", "space_id", "start_time", "end_time", "total_amount"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        start_time = datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M:%S")
        end_time = datetime.strptime(data["end_time"], "%Y-%m-%dT%H:%M:%S")

        # Check if space is available
        space = Space.query.get(data["space_id"])
        if not space or not space.availability:
            return jsonify({"error": "Space is not available"}), 409

        new_booking = Booking(
            user_id=data["user_id"],
            space_id=data["space_id"],
            start_time=start_time,
            end_time=end_time,
            total_amount=data["total_amount"],
            status="Pending Payment"
        )

        db.session.add(new_booking)
        db.session.commit()

        return jsonify({"message": "Booking created successfully", "id": new_booking.id}), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"🚨 Error creating booking: {e}")
        return jsonify({"error": "An error occurred while processing the booking"}), 500

#! ✅ FETCH ALL BOOKINGS
@booking_bp.route("/bookings", methods=['GET'])
def fetch_all_bookings():
    try:
        # Fetch all bookings from the database
        bookings = Booking.query.all()
        
        # Convert each booking to a dictionary using the to_dict method
        bookings_list = [booking.to_dict() for booking in bookings]
        
        # Return the list of bookings as a JSON response
        return jsonify(bookings_list), 200
    
    except Exception as e:
        # Log the error for debugging
        logging.error(f"🚨 Error fetching all bookings: {e}")
        
        # Return a 500 Internal Server Error with a user-friendly message
        return jsonify({"error": "An error occurred while fetching bookings"}), 500


#! ✅ FETCH SINGLE BOOKING
@booking_bp.route("/bookings/<int:booking_id>", methods=['GET'])
def get_booking(booking_id):
    try:
        # Fetch the booking by its ID
        booking = Booking.query.get(booking_id)
        
        # If the booking doesn't exist, return a 404 Not Found error
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        # Convert the booking to a dictionary using the to_dict method
        booking_dict = booking.to_dict()
        
        # Return the booking details as a JSON response
        return jsonify(booking_dict), 200
    
    except Exception as e:
        # Log the error for debugging
        logging.error(f"🚨 Error fetching booking with ID {booking_id}: {e}")
        
        # Return a 500 Internal Server Error with a user-friendly message
        return jsonify({"error": "An error occurred while fetching the booking"}), 500

#! ✅ UPDATE BOOKING STATUS
@booking_bp.route("/bookings/<int:booking_id>/status", methods=['PATCH'])
def update_booking_status(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    data = request.get_json()
    if "status" not in data:
        return jsonify({"error": "Missing status field"}), 400

    booking.status = data["status"]
    db.session.commit()

    return jsonify({"message": "Booking status updated successfully"}), 200

#! ✅ DELETE BOOKING
@booking_bp.route("/bookings/<int:booking_id>", methods=['DELETE'])
def delete_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    db.session.delete(booking)
    db.session.commit()

    return jsonify({"message": "Booking deleted successfully"}), 200