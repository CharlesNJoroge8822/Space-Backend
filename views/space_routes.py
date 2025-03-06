from flask import Blueprint, request, jsonify
from models import Space, db, Booking
import logging

space_bp = Blueprint("space_bp", __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#! ✅ CREATE SPACE (Default Availability: True)
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    data = request.get_json()

    required_fields = ["name", "description", "location", "price_per_hour", "price_per_day"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_space = Space(
        name=data["name"],
        description=data["description"],
        location=data["location"],
        price_per_hour=data["price_per_hour"],
        price_per_day=data["price_per_day"],
        availability=True,  # Default to Available
        images=data.get("images")
    )

    db.session.add(new_space)
    db.session.commit()

    return jsonify(new_space.to_dict()), 201

#! ✅ FETCH ALL SPACES
@space_bp.route("/spaces", methods=["GET"])
def get_all_spaces():
    try:
        spaces = Space.query.all()
        if not spaces:
            logger.warning("⚠️ No spaces found in the database.")
            return jsonify({"message": "No spaces available."}), 200

        spaces_list = [
            {
                "id": space.id,
                "name": space.name,
                "description": space.description,
                "location": space.location,
                "price_per_hour": space.price_per_hour,
                "price_per_day": space.price_per_day,
                "availability": space.availability,
                "images": space.images,
            }
            for space in spaces
        ]
        return jsonify({"spaces": spaces_list}), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching spaces: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
    
#! ✅ FETCH SINGLE SPACE (With Booking Details)
@space_bp.route("/spaces/<int:space_id>", methods=['GET'])
def get_space(space_id):
    space = Space.query.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify(space.to_dict()), 200

#! ✅ UPDATE SPACE DETAILS
@space_bp.route("/spaces/<int:space_id>", methods=['PATCH'])
def update_space(space_id):
    space = Space.query.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    
    data = request.get_json()
    for key, value in data.items():
        if hasattr(space, key):
            setattr(space, key, value)
    
    db.session.commit()
    return jsonify({"message": "Space updated successfully"}), 200

#! ✅ UPDATE SPACE AVAILABILITY
@space_bp.route("/spaces/<int:space_id>/availability", methods=['PATCH'])
def update_space_availability(space_id):
    space = Space.query.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404

    data = request.get_json()
    if "availability" not in data:
        return jsonify({"error": "Missing availability field"}), 400

    active_bookings = Booking.query.filter(
        Booking.space_id == space_id,
        Booking.status.in_(["Booked", "Pending Payment"])
    ).count()

    if data["availability"] and active_bookings > 0:
        return jsonify({"error": "Cannot mark space as available while there are active bookings"}), 400

    space.availability = data["availability"]
    db.session.commit()

    return jsonify({
        "id": space.id,
        "availability": space.availability,
        "message": f"Space status updated to {'Available' if space.availability else 'Booked'}"
    }), 200

#! ✅ DELETE SPACE (Ensure No Active Bookings Exist)
@space_bp.route("/spaces/<int:space_id>", methods=['DELETE'])
def delete_space(space_id):
    space = Space.query.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404

    active_bookings = Booking.query.filter(
        Booking.space_id == space.id,
        Booking.status.in_(["Booked", "Pending Payment"])
    ).count()

    if active_bookings > 0:
        return jsonify({"error": "Cannot delete space with active or pending bookings"}), 400

    db.session.delete(space)
    db.session.commit()

    return jsonify({"message": "Space deleted successfully"}), 200