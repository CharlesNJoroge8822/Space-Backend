from flask import Blueprint, request, jsonify
from models import Space, db, Booking
import logging

space_bp = Blueprint("space_bp", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! ✅ CREATE SPACE (Default Status: "Available")
@space_bp.route("/spaces", methods=['POST'])
def create_space():
    try:
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
            status="Available",  # Default status
            images=data.get("images", "")  # Default to empty string if not provided
        )

        db.session.add(new_space)
        db.session.commit()

        return jsonify({
            "message": "Space created successfully",
            "data": new_space.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error creating space: {e}")
        return jsonify({"error": "An error occurred while creating the space"}), 500


#! ✅ FETCH ALL SPACES
@space_bp.route("/spaces", methods=["GET"])
def get_all_spaces():
    try:
        spaces = Space.query.all()
        if not spaces:
            logger.warning("⚠️ No spaces found in the database.")
            return jsonify({"message": "No spaces available.", "data": []}), 200

        spaces_list = [space.to_dict() for space in spaces]  # Use to_dict method
        return jsonify({
            "message": "Spaces fetched successfully",
            "data": spaces_list
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching spaces: {e}")
        return jsonify({"error": "An error occurred while fetching spaces"}), 500


#! ✅ FETCH SINGLE SPACE
@space_bp.route("/spaces/<int:space_id>", methods=['GET'])
def get_space(space_id):
    try:
        space = Space.query.get(space_id)
        if not space:
            return jsonify({"error": "Space not found"}), 404

        return jsonify({
            "message": "Space fetched successfully",
            "data": space.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching space with ID {space_id}: {e}")
        return jsonify({"error": "An error occurred while fetching the space"}), 500


#! ✅ UPDATE SPACE DETAILS
@space_bp.route("/spaces/<int:space_id>", methods=['PATCH'])
def update_space(space_id):
    try:
        space = Space.query.get(space_id)
        if not space:
            return jsonify({"error": "Space not found"}), 404

        data = request.get_json()
        for key, value in data.items():
            if hasattr(space, key):
                setattr(space, key, value)

        db.session.commit()
        return jsonify({
            "message": "Space updated successfully",
            "data": space.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error updating space with ID {space_id}: {e}")
        return jsonify({"error": "An error occurred while updating the space"}), 500


#! ✅ UPDATE SPACE STATUS
@space_bp.route("/spaces/<int:space_id>/status", methods=['PATCH'])
def update_space_status(space_id):
    try:
        space = Space.query.get(space_id)
        if not space:
            return jsonify({"error": "Space not found"}), 404

        data = request.get_json()
        if "status" not in data:
            return jsonify({"error": "Missing status field"}), 400

        active_bookings = Booking.query.filter(
            Booking.space_id == space_id,
            Booking.status.in_(["Confirmed", "Pending Payment"])
        ).count()

        if data["status"] == "Available" and active_bookings > 0:
            return jsonify({"error": "Cannot mark space as available while there are active bookings"}), 400

        space.status = data["status"]
        db.session.commit()

        return jsonify({
            "message": "Space status updated successfully",
            "data": space.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error updating space status with ID {space_id}: {e}")
        return jsonify({"error": "An error occurred while updating the space status"}), 500


#! ✅ DELETE SPACE
@space_bp.route("/spaces/<int:space_id>", methods=['DELETE'])
def delete_space(space_id):
    try:
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

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error deleting space with ID {space_id}: {e}")
        return jsonify({"error": "An error occurred while deleting the space"}), 500