from flask import jsonify, request, Blueprint
from models import db, User, TokenBlockList  # ✅ Ensure correct import
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)

auth_bp = Blueprint("auth_bp", __name__)

# ✅ LOGIN
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


# ✅ GET CURRENT USER
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


# ✅ LOGOUT
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """Blacklist a token on logout."""
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlockList(jti=jti, created_at=now))  # ✅ Fix model reference
    db.session.commit()
    return jsonify({"success": "Logged out successfully"}), 200


# ✅ REGISTER USER (Updated for Compatibility)
@auth_bp.route("/users", methods=["POST"])
def register_user():
    """Registers a new user."""
    data = request.get_json()

    # ✅ Validate all required fields
    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]
    role = data.get("role", "Client").strip().capitalize()  # ✅ Default role = "Client"

    # ✅ Ensure role matches allowed values (optional)
    allowed_roles = ["Client", "Admin"]
    if role not in allowed_roles:
        return jsonify({"error": f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"}), 400

    # ✅ Check for existing user
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    # ✅ Hash password and create user
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
