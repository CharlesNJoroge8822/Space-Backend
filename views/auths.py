from flask import jsonify, request, Blueprint
from models import db, User, TokenBlockList  #! ✅ Ensure correct import
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt, decode_token
)
import re

auth_bp = Blueprint("auth_bp", __name__)

#! ✅ LOGIN
@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "No user found with this email"}), 401
    if not check_password_hash(user.password, password):
        return jsonify({"error": "Incorrect password"}), 401

    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=1))

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_admin": user.role.lower() == "admin"
        }
    }), 200


#! ✅ GET CURRENT USER
@auth_bp.route("/current_user", methods=["GET"])
@jwt_required()
def current_user():
    """Get details of the logged-in user."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_admin": user.role.lower() == "admin"
    }), 200


#! ✅ LOGOUT
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """Blacklist a token on logout."""
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlockList(jti=jti, created_at=now))  #! ✅ Fix model reference
    db.session.commit()
    return jsonify({"success": "Logged out successfully"}), 200


#! ✅ REGISTER USER (Updated for Compatibility)
@auth_bp.route("/users", methods=["POST"])
def register_user():
    """Registers a new user."""
    data = request.get_json()

    #! ✅ Validate all required fields
    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]
    role = data.get("role", "Client").strip().capitalize()  #! ✅ Default role = "Client"

    #! ✅ Ensure role matches allowed values (optional)
    allowed_roles = ["Client", "Admin"]
    if role not in allowed_roles:
        return jsonify({"error": f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"}), 400

    #! ✅ Check for existing user
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    #! ✅ Hash password and create user
    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "msg": "User registered successfully.",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    }), 201
    

# ! User sends a request for wanting to reset their password ..
@auth_bp.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    """Generate a password reset token and send it to the user."""
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No user found with this email"}), 404

    reset_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=15))

    return jsonify({"msg": "Password reset token generated.", "reset_token": reset_token}), 200


#! ✅ RESET PASSWORD (Using Token)
@auth_bp.route("/reset_password", methods=["POST"])
def reset_password():
    """Reset the user's password using a reset token."""
    
    data = request.get_json()
    reset_token = data.get("reset_token")
    new_password = data.get("new_password")

    if not reset_token or not new_password:
        return jsonify({"error": "Reset token and new password are required"}), 400

    try:
        decoded_token = decode_token(reset_token)
        user_id = decoded_token["sub"]
    except Exception as e:
        return jsonify({"error": "Invalid or expired reset token"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    #! ✅ Validate password strength
    if not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$", new_password):
        return jsonify({"error": "Password must be at least 6 characters long, "
                                 "contain one uppercase letter, one number, and one special character (@$!%*?&)."}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"msg": "Password reset successfully."}), 200

