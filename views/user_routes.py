from flask import Blueprint, request, jsonify
from models import User, db
from werkzeug.security import generate_password_hash
import re  
from flask_jwt_extended import jwt_required, get_jwt_identity  # ✅ Ensure authentication

user_bp = Blueprint("user_bp", __name__)

PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# ✅ Ensure admin authentication
def is_admin():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role.lower() == 'admin'

# ✅ CREATE USER
@user_bp.route("/users", methods=['POST'])
@jwt_required()  # ✅ Requires authentication
def create_user():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image = data.get('image', 'default.jpg')  # ✅ Default image
    role = data.get('role', 'Client').capitalize()  # ✅ Default role is 'Client'

    # ✅ Ensure role is valid
    if role not in ["Client", "Admin"]:
        return jsonify({"error": "Invalid role. Allowed roles: 'Client', 'Admin'"}), 400

    if not all([name, email, password]):
        return jsonify({"error": "Name, email, and password are required"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email format"}), 400

    if not re.match(PASSWORD_REGEX, password):
        return jsonify({
            "error": "Password must be at least 6 characters long, contain one uppercase letter, one number, and one special character (@$!%*?&)"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    # ✅ Hash password
    hashed_password = generate_password_hash(password)

    # ✅ Create new user
    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        image=image,
        role=role
    )

    # ✅ Save to database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "image": new_user.image,
            "created_at": new_user.created_at
        }
    }), 201  

# ✅ FETCH SINGLE USER
@user_bp.route("/users/<int:id>", methods=['GET'])
@jwt_required()
def fetch_user(id):
    user = User.query.get(id)

    if not user:
        return jsonify({"error": "User with ID not found"}), 404
    
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "image": user.image,
        "created_at": user.created_at
    }), 200  

# ✅ FETCH ALL USERS (Admin Only)
@user_bp.route("/users", methods=['GET'])
@jwt_required()
def fetch_all_users():
    if not is_admin():
        return jsonify({"error": "Only admins can access this resource"}), 403

    users = User.query.all()
    
    users_list = [{
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "image": user.image,
        "created_at": user.created_at
    } for user in users]

    return jsonify(users_list), 200

# ✅ UPDATE USER (Self or Admin Only)
@user_bp.route("/users/<int:id>", methods=['PATCH'])
@jwt_required()
def update_user(id):
    current_user_id = get_jwt_identity()
    user = User.query.get(id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # ✅ Allow self-update or admin update only
    if current_user_id != user.id and not is_admin():
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    
    # ✅ Validate and update fields if provided
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if name:
        if len(name) < 3:
            return jsonify({"error": "Name must be at least 3 characters long"}), 400
        user.name = name

    if email:
        if not re.match(EMAIL_REGEX, email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # ✅ Ensure email is unique
        existing_user = User.query.filter_by(email=email).filter(User.id != id).first()
        if existing_user:
            return jsonify({"error": "Email already in use"}), 409
        
        user.email = email

    if password:
        if not re.match(PASSWORD_REGEX, password):
            return jsonify({
                "error": "Password must be at least 6 characters long, contain one uppercase letter, one number, and one special character (@$!%*?&)"
            }), 400
        
        user.password = generate_password_hash(password)

    # ✅ Commit changes to the database
    db.session.commit()

    return jsonify({
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200

# ✅ DELETE USER (Admin Only)
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # ✅ Ensure admin rights
    if not is_admin():
        return jsonify({"error": "Only admins can delete users"}), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200
