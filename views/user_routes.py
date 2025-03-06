from flask import Blueprint, request, jsonify
from models import User, db
from werkzeug.security import generate_password_hash
import re
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

user_bp = Blueprint("user_bp", __name__)

PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! ✅ CREATE USER
@user_bp.route("/users", methods=['POST'])
def create_user():
    try:
        data = request.get_json()

        required_fields = ["name", "email", "password"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        if not re.match(EMAIL_REGEX, data["email"]):
            return jsonify({"error": "Invalid email format"}), 400

        if not re.match(PASSWORD_REGEX, data["password"]):
            return jsonify({"error": "Password must be at least 6 characters long, contain one uppercase letter, one number, and one special character (@$!%*?&)"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already in use"}), 409

        new_user = User(
            name=data["name"],
            email=data["email"],
            password=generate_password_hash(data["password"]),
            role=data.get("role", "Client").capitalize(),
            image=data.get("image", "default.jpg")
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "data": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "image": new_user.image
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error creating user: {e}")
        return jsonify({"error": "An error occurred while creating the user"}), 500


#! ✅ FETCH USER BY ID
@user_bp.route("/users/<int:user_id>", methods=['GET'])
def fetch_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "message": "User fetched successfully",
            "data": user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching user with ID {user_id}: {e}")
        return jsonify({"error": "An error occurred while fetching the user"}), 500


#! ✅ FETCH ALL USERS (Admin Only)
@user_bp.route("/users", methods=['GET'])
# @jwt_required()
def fetch_all_users():
    try:
        # current_user_id = get_jwt_identity()
        # current_user = User.query.get(current_user_id)

        # if not current_user or current_user.role != "Admin":
        #     return jsonify({"error": "Only admins can access this resource"}), 403

        users = User.query.all()
        users_list = [user.to_dict() for user in users]

        return jsonify({
            "message": "Users fetched successfully",
            "data": users_list
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching all users: {e}")
        return jsonify({"error": "An error occurred while fetching users"}), 500


#! ✅ UPDATE USER
@user_bp.route("/users/<int:user_id>", methods=['PATCH'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        if current_user_id != user.id and User.query.get(current_user_id).role != "Admin":
            return jsonify({"error": "Unauthorized to update this user"}), 403

        data = request.get_json()
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()

        return jsonify({
            "message": "User updated successfully",
            "data": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error updating user with ID {user_id}: {e}")
        return jsonify({"error": "An error occurred while updating the user"}), 500


#! ✅ DELETE USER (Admin Only)
@user_bp.route("/users/<int:user_id>", methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or current_user.role != "Admin":
            return jsonify({"error": "Only admins can delete users"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error deleting user with ID {user_id}: {e}")
        return jsonify({"error": "An error occurred while deleting the user"}), 500