from flask import Blueprint, request, jsonify
from models import Booking, db
from datetime import datetime
import re
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

booking_bp = Blueprint("booking_bp", __name__)

# Validate date format function
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")  # Expected format: YYYY-MM-DD
        return True
    except ValueError:
        return False
@booking_bp.route("/bookings", methods=['POST'])
def create_booking():
    try:
        data = request.get_json()

        user_id = data.get('user_id')
        space_id = data.get('space_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        total_amount = data.get('total_amount', 0.0)  # Default to 0 if not provided
        status = data.get('status', "Pending Payment")  # Default status is "Pending Payment"

        # Validate inputs
        if not user_id or not space_id or not start_time or not end_time:
            return jsonify({"error": "Missing required fields (user_id, space_id, start_time, end_time)"}), 400

        # Convert start_time and end_time to datetime format
        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
            end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS"}), 400

        # Check if a booking already exists for this time slot
        existing_booking = Booking.query.filter_by(user_id=user_id, space_id=space_id, start_time=start_time).first()
        if existing_booking:
            return jsonify({"error": "Booking already exists for this user at this time"}), 409

        # Create a new booking
        new_booking = Booking(
            user_id=user_id,
            space_id=space_id,
            start_time=start_time,
            end_time=end_time,
            total_amount=total_amount,
            status=status  # Set initial status
        )

        db.session.add(new_booking)
        db.session.commit()

        return jsonify({
            "id": new_booking.id,
            "user_id": new_booking.user_id,
            "space_id": new_booking.space_id,
            "start_time": new_booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": new_booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_amount": new_booking.total_amount,
            "status": new_booking.status
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while processing the booking", "details": str(e)}), 500

# Fetch Booking by ID
@booking_bp.route("/bookings/<int:id>", methods=['GET'])
def fetch_booking(id):
    try:
        booking = Booking.query.get(id)

        if booking is None:
            return jsonify({"error": "Booking not found"}), 404

        return jsonify({
            "id": booking.id,
            "user_id": booking.user_id,
            "space_id": booking.space_id,
            "start_time": booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_amount": booking.total_amount,
            "status": booking.status
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch booking", "details": str(e)}), 500

# Fetch all Bookings with Pagination
@booking_bp.route("/bookings", methods=['GET'])
def fetch_all_bookings():
    try:
        bookings_page = request.args.get('page', 1, type=int)
        per_booking_page = request.args.get('per_page', 10, type=int)
        
        paginated_bookings = Booking.query.paginate(page=bookings_page, per_page=per_booking_page, error_out=False)

        bookings_list = [{
            "id": booking.id,
            "user_id": booking.user_id,
            "space_id": booking.space_id,
            "start_time": booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_amount": booking.total_amount,
            "status": booking.status
        } for booking in paginated_bookings.items]

        return jsonify({
            "bookings": bookings_list,
            "total_bookings": paginated_bookings.total,
            "total_pages": paginated_bookings.pages,
            "current_page_number": paginated_bookings.page
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch bookings", "details": str(e)}), 500

# Update Booking Status
@booking_bp.route("/bookings/<int:id>/status", methods=['PATCH'])
def update_booking_status(id):
    try:
        booking = Booking.query.get(id)

        if booking is None:
            return jsonify({"error": "Booking not found"}), 404

        data = request.get_json()
        if "status" not in data:
            return jsonify({"error": "Missing status field"}), 400

        # Update the booking status
        booking.status = data["status"]
        db.session.commit()

        return jsonify({
            "id": booking.id,
            "status": booking.status,
            "message": "Booking status updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update booking status", "details": str(e)}), 500

# Delete Booking
@booking_bp.route('/bookings/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_booking(id):
    try:
        # Debug: Log received JWT token
        auth_header = request.headers.get("Authorization")
        print("Received Authorization Header:", auth_header)

        # Extract the user ID from the token
        current_user_id = get_jwt_identity()
        print("Decoded JWT User ID:", current_user_id)

        # Retrieve the booking
        booking = Booking.query.get(id)

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Ensure the user owns the booking OR is an admin
        if booking.user_id != current_user_id:
            return jsonify({"error": "Unauthorized to delete this booking"}, 403)

        # Delete the booking
        db.session.delete(booking)
        db.session.commit()

        return jsonify({"message": "Booking deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete booking", "details": str(e)}), 500
