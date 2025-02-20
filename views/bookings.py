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
    }), 200
    
# Fetch al bookings ..
@booking_bp.route("/bookings", methods=['GET'])
def fetch_all_bookings():
    bookings_page = request.args.get('page', 1, type=int)
    per_booking_page = request.args.get('per_page', 10, type=int)
    
    paginated_bookings = Booking.query.paginate(page=bookings_page, per_page=per_booking_page, error_out=False)

    bookings_list = [{
        "id": booking.id,
        "user_id": booking.user_id,
        "space_id": booking.space_id,
        "date": booking.date
    } for booking in paginated_bookings.items]

    return jsonify({
        "bookings": bookings_list,
        "total_bookings": paginated_bookings.total,
        "total_pages": paginated_bookings.pages,
        "current_page_number": paginated_bookings.page
    }), 200


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

    return jsonify({"msg": "Booking deleted successfully"}), 200
