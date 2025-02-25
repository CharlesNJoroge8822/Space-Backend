from flask import Blueprint, request, jsonify
from models import Space, db

space_bp = Blueprint("space_bp", __name__)

#! ✅ CREATE SPACE
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    data = request.get_json()

    name = data.get("name")
    description = data.get("description")
    location = data.get("location")
    price_per_hour = data.get("price_per_hour")
    price_per_day = data.get("price_per_day")
    availability = data.get("availability")  #! JSON string
    images = data.get("images")  #! Comma-separated URLs

    #! ✅ Validate required fields
    if not all([name, description, location, price_per_hour, price_per_day, availability]):
        return jsonify({"error": "Missing required fields"}), 400

    #! ✅ Check if space already exists
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

    #! ✅ Save to database
    db.session.add(new_space)
    db.session.commit()

    return jsonify({
        "id": new_space.id,
        "name": new_space.name,
        "description": new_space.description,
        "location": new_space.location,
        "price_per_hour": new_space.price_per_hour,
        "price_per_day": new_space.price_per_day,
        "availability": new_space.availability,
        "images": new_space.images
    }), 201


#! ✅ FETCH ALL SPACES
@space_bp.route("/spaces", methods=['GET'])
def get_all_spaces():
    # ! Pagination Variables
    space = request.args.get('page', 1, type=int)  # Page number
    per_space = request.args.get('per_page', 10, type=int)  # Items per page

    # ! Corrected Pagination Query
    paginated_spaces = Space.query.paginate(page=space, per_page=per_space, error_out=False)

    # ! Loop Through Paginated Results
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

    # ! Return Paginated Data
    return jsonify({
        "spaces": spaces_list,
        "total_spaces": paginated_spaces.total,  # Total spaces in DB
        "total_pages": paginated_spaces.pages,  # Total pages
        "current_page_number": paginated_spaces.page,  # Current page number
        "spaces_per_page": paginated_spaces.per_page  # Spaces per page
    }), 200


#! ✅ FETCH SINGLE SPACE
@space_bp.route("/spaces/<int:space_id>", methods=['GET'])
def get_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    return jsonify({
        "id": space.id,
        "name": space.name,
        "description": space.description,
        "location": space.location,
        "price_per_hour": space.price_per_hour,
        "price_per_day": space.price_per_day,
        "availability": space.availability,
        "images": space.images
    }), 200

#! ✅ UPDATE SPACE
@space_bp.route("/spaces/<int:space_id>", methods=['PATCH'])
def update_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    data = request.get_json()

    #! ✅ Update only the provided fields
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
        space.availability = data["availability"]
    if "images" in data:
        space.images = data["images"]

    db.session.commit()

    return jsonify({"message": "Space updated successfully"}), 200

#! ✅ DELETE SPACE
@space_bp.route("/spaces/<int:space_id>", methods=['DELETE'])
def delete_space(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    db.session.delete(space)
    db.session.commit()

    return jsonify({"message": "Space deleted successfully"}), 200
