from flask import Blueprint, request, jsonify
from models import Space, db

space_bp = Blueprint("space_bp", __name__)

# Create Space
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    data = request.get_json()
    
    name = data.get('name')
    location = data.get('location')
    price = data.get('price')

    # Check if space already exists
    existing_space = Space.query.filter_by(name=name).first()
    if existing_space:
        return jsonify({"error": "Space with this name already exists"}), 400

    new_space = Space(name=name, location=location, price=price)

    # Add and commit to DB
    db.session.add(new_space)
    db.session.commit()

    return jsonify({
        "id": new_space.id,
        "name": new_space.name,
        "location": new_space.location,
        "price": new_space.price
    }), 201

# Fetch Space by ID
@space_bp.route("/spaces/<int:id>", methods=['GET'])
def fetch_space(id):
    space = Space.query.get(id)

    if space is None:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({
        "id": space.id,
        "name": space.name,
        "location": space.location,
        "price": space.price
    })

# Update Space
@space_bp.route("/spaces/<int:id>", methods=['PATCH'])
def update_space(id):
    space = Space.query.get(id)

    if space is None:
        return jsonify({"error": "Space not found"}), 404
    
    data = request.get_json()

    name = data.get("name")
    location = data.get("location")
    price = data.get("price")

    if name:
        space.name = name
    if location:
        space.location = location
    if price:
        space.price = price

    db.session.commit()

    return jsonify({
        "id": space.id,
        "name": space.name,
        "location": space.location,
        "price": space.price
    }), 200

# Delete Space
@space_bp.route('/spaces/<int:id>', methods=['DELETE'])
def delete_space(id):
    space = Space.query.get(id)

    if space is None:
        return jsonify({"error": "Space not found"}), 404

    db.session.delete(space)
    db.session.commit()

    return jsonify({"msg": "Space deleted successfully"}), 200
