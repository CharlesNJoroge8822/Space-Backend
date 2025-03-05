from flask import Blueprint, request, jsonify
from models import Space, db, Booking

space_bp = Blueprint("space_bp", __name__)

#! ✅ CREATE SPACE (Default Availability: "Available")
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    data = request.get_json()

    name = data.get("name")
    description = data.get("description")
    location = data.get("location")
    price_per_hour = data.get("price_per_hour")
    price_per_day = data.get("price_per_day")
    availability = data.get("availability", "Available")  # ✅ Default to "Available"
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

    return jsonify({
        "id": new_space.id,
        "name": new_space.name,
        "description": new_space.description,
        "location": new_space.location,
        "price_per_hour": new_space.price_per_hour,
        "price_per_day": new_space.price_per_day,
        "availability": new_space.availability,  # ✅ Returns actual availability
        "images": new_space.images
    }), 201


#! ✅ FETCH ALL SPACES (Paginated)
@space_bp.route("/spaces", methods=['GET'])
def get_all_spaces():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated_spaces = Space.query.paginate(page=page, per_page=per_page, error_out=False)

    spaces_list = [{
        "id": space.id,
        "name": space.name,
        "description": space.description,
        "location": space.location,
        "price_per_hour": space.price_per_hour,
        "price_per_day": space.price_per_day,
        "availability": space.availability,
        "images": space.images
    } for space in paginated_spaces.items]

    return jsonify({
        "spaces": spaces_list,
        "total_spaces": paginated_spaces.total,
        "total_pages": paginated_spaces.pages,
        "current_page_number": paginated_spaces.page,
        "spaces_per_page": paginated_spaces.per_page
    }), 200


#! ✅ FETCH SINGLE SPACE (Includes Booking Details)
@space_bp.route("/spaces/<int:space_id>", methods=['GET'])
def get_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    bookings = Booking.query.filter_by(space_id=space.id).all()

    space_data = {
        "id": space.id,
        "name": space.name,
        "description": space.description,
        "location": space.location,
        "price_per_hour": space.price_per_hour,
        "price_per_day": space.price_per_day,
        "availability": space.availability,
        "images": space.images,
        "bookings": [
            {
                "id": booking.id,
                "user_id": booking.user_id,
                "start_time": booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_time": booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_amount": booking.total_amount,
                "status": booking.status,
                "user_details": {
                    "id": booking.user.id,
                    "name": booking.user.name,
                    "email": booking.user.email,
                    "image": booking.user.image,
                } if booking.user else None,
            }
            for booking in bookings
        ],
    }

    return jsonify(space_data), 200


#! ✅ UPDATE SPACE DETAILS
@space_bp.route("/spaces/<int:space_id>", methods=['PATCH'])
def update_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    data = request.get_json()

    if "name" in data:
        space.name = data["name"]
    if "description" in data:
        space.description = data["description"]
    if "location" in data:
        space.location = data["location"]
    if "price_per_hour" in data:
        space.price_per_hour = data["price_per_hour"]
    if "price_per_day" in data:
        space.price_per_day = data["price_per_day"]
    if "availability" in data:
        space.availability = data["availability"]  # ✅ Update availability
    if "images" in data:
        space.images = data["images"]

    db.session.commit()

    return jsonify({"message": "Space updated successfully"}), 200


#! ✅ UPDATE SPACE AVAILABILITY (After Booking & Payment)
@space_bp.route("/spaces/<int:space_id>/availability", methods=['PATCH'])
def update_space_availability(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    data = request.get_json()
    if "availability" not in data:
        return jsonify({"error": "Missing availability field"}), 400

    space.availability = "Booked" if not data["availability"] else "Available"
    db.session.commit()

    return jsonify({
        "id": space.id,
        "availability": space.availability,
        "message": f"Space status updated to {space.availability}"
    }), 200


#! ✅ DELETE SPACE (Only if No Active Bookings)
@space_bp.route("/spaces/<int:space_id>", methods=['DELETE'])
def delete_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    active_bookings = Booking.query.filter_by(space_id=space.id, status="Confirmed").count()
    if active_bookings > 0:
        return jsonify({"error": "Cannot delete space with active bookings"}), 400

    db.session.delete(space)
    db.session.commit()

    return jsonify({"message": "Space deleted successfully"}), 200
