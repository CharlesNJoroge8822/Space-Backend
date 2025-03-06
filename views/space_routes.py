from flask import Blueprint, request, jsonify
from models import Space, db, Booking

space_bp = Blueprint("space_bp", __name__)

#! ✅ CREATE SPACE (Default Availability: True)
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    data = request.get_json()

    name = data.get("name")
    description = data.get("description")
    location = data.get("location")
    price_per_hour = data.get("price_per_hour")
    price_per_day = data.get("price_per_day")
    availability = data.get("availability", True)  # ✅ Default to True (Available)
    images = data.get("images")

    if not all([name, description, location, price_per_hour, price_per_day]):
        return jsonify({"error": "Missing required fields"}), 400

    existing_space = Space.query.filter_by(name=name).first()
    if existing_space:
        return jsonify({"error": "Space with this name already exists"}), 400

    new_space = Space(
        name=name,
        description=description,
        location=location,
        price_per_hour=price_per_hour,
        price_per_day=price_per_day,
        availability=availability,
        images=images
    )

    db.session.add(new_space)
    db.session.commit()

    return jsonify(new_space.to_dict()), 201

#! ✅ FETCH ALL SPACES
@space_bp.route("/spaces", methods=['GET'])
def get_all_spaces():
    spaces = Space.query.all()
    return jsonify([space.to_dict() for space in spaces]), 200

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

#! ✅ DELETE SPACE (Only If No Active Bookings Exist)
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

    return jsonify({"message": "Space deleted successfully"}),200
