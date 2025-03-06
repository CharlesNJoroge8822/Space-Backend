from flask import Blueprint, request, jsonify
from models import Booking, db, Space, User
from datetime import datetime
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity

booking_bp = Blueprint("booking_bp", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! ✅ CREATE BOOKING
@booking_bp.route("/bookings", methods=['POST'])
def create_booking():
    try:
        data = request.get_json()

        required_fields = ["user_id", "space_id", "start_time", "end_time", "total_amount"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        start_time = datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M:%S")
        end_time = datetime.strptime(data["end_time"], "%Y-%m-%dT%H:%M:%S")

        space = Space.query.get(data["space_id"])
        if not space or space.status != "Available":
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

        return jsonify({
            "message": "Booking created successfully",
            "data": new_booking.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error creating booking: {e}")
        return jsonify({"error": "An error occurred while creating the booking"}), 500

#! ✅ FETCH USER'S BOOKINGS
#! ✅ FETCH USER'S BOOKINGS
@booking_bp.route("/my-bookings", methods=['GET'])
def fetch_user_bookings():
    try:
        user_id = request.args.get("user_id")  # Get user_id from query parameter
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        bookings = Booking.query.filter_by(user_id=user_id).all()
        bookings_list = [booking.to_dict() for booking in bookings]

        return jsonify({
            "message": "User bookings fetched successfully",
            "data": bookings_list
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching user's bookings: {e}")
        return jsonify({"error": "An error occurred while fetching user bookings"}), 500



#! ✅ FETCH ALL BOOKINGS
@booking_bp.route("/bookings", methods=['GET'])
def fetch_all_bookings():
    try:
        bookings = Booking.query.all()
        bookings_list = [booking.to_dict() for booking in bookings]

        return jsonify({
            "message": "Bookings fetched successfully",
            "data": bookings_list
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching all bookings: {e}")
        return jsonify({"error": "An error occurred while fetching bookings"}), 500


#! ✅ FETCH SINGLE BOOKING
@booking_bp.route("/bookings/<int:booking_id>", methods=['GET'])
def get_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        return jsonify({
            "message": "Booking fetched successfully",
            "data": booking.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching booking with ID {booking_id}: {e}")
        return jsonify({"error": "An error occurred while fetching the booking"}), 500


#! ✅ UPDATE BOOKING STATUS
@booking_bp.route("/bookings/<int:booking_id>/status", methods=['PATCH'])
def update_booking_status(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        data = request.get_json()
        if "status" not in data:
            return jsonify({"error": "Missing status field"}), 400

        booking.status = data["status"]
        db.session.commit()

        return jsonify({
            "message": "Booking status updated successfully",
            "data": booking.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error updating booking status with ID {booking_id}: {e}")
        return jsonify({"error": "An error occurred while updating the booking status"}), 500


#! ✅ DELETE BOOKING
@booking_bp.route("/bookings/<int:booking_id>", methods=['DELETE'])
def delete_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        db.session.delete(booking)
        db.session.commit()

        return jsonify({"message": "Booking deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error deleting booking with ID {booking_id}: {e}")
        return jsonify({"error": "An error occurred while deleting the booking"}), 500