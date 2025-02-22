from flask import Blueprint, request, jsonify
from models import User, Payment, db
from werkzeug.security import generate_password_hash
import re  

user_bp = Blueprint("user_bp", __name__)
payment_bp = Blueprint("payment_bp", __name__)

PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$"
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def is_admin(user):
    return user and user.role == 'Admin'

# ✅ CREATE USER
@user_bp.route("/users", methods=['POST'])
def create_user():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image = data.get('image')
    role = data.get('role', 'Client')  # Default role is 'Client'

    if not all([name, email, password]):
        return jsonify({"error": "Name, email, and password are required"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email format"}), 400

    check_email = User.query.filter_by(email=email).first()
    check_name = User.query.filter_by(name=name).first()

    if check_email or check_name:
        return jsonify({"error": "User with Email or Username already exists"}), 400

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
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "image": new_user.image,
        "created_at": new_user.created_at
    }), 201  

# ✅ FETCH SINGLE USER
@user_bp.route("/users/<int:id>", methods=['GET'])
def fetch_user(id):
    user = User.query.get(id)
    # !pagination vars

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

# ✅ FETCH ALL USERS
@user_bp.route("/users", methods=['GET'])
def fetch_all_users():
    # ! Pagination Variables
    page = request.args.get('page', 1, type=int)  # Page number
    per_page = request.args.get('per_page', 10, type=int)  # Items per page

    # ! Correct Pagination Query
    paginated_users = User.query.paginate(page=page, per_page=per_page, error_out=False)

    # ! Loop Through Paginated Results
    users_list = [{
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "image": user.image,
        "created_at": user.created_at
    } for user in paginated_users.items]

    # ! Return Paginated Data
    return jsonify({
        "users": users_list,
        "total_users": paginated_users.total,  # Total users in DB
        "total_pages": paginated_users.pages,  # Total pages
        "current_page_number": paginated_users.page  # Current page number
    }), 200


# ✅ UPDATE USER
@user_bp.route("/users/<int:id>", methods=['PATCH'])
def update_user(id):
    user = User.query.get(id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    
    # Validate and update fields if provided
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
        
        # Ensure email is unique
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
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 200

# ✅ DELETE USER (Admin Only)
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # ✅ Ensure admin rights (Replace with actual authentication logic)
    if not is_admin(user):
        return jsonify({"error": "Only admins can delete users"}), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200

# ✅ CREATE PAYMENT
@payment_bp.route("/payments", methods=['POST'])
def create_payment():
    data = request.get_json()

    new_payment = Payment(**data)
    db.session.add(new_payment)
    db.session.commit()

    return jsonify(new_payment.to_dict()), 201

# ✅ FETCH PAYMENT BY ID
@payment_bp.route("/payments/<int:id>", methods=['GET'])
def fetch_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify(payment.to_dict())

# ✅ UPDATE PAYMENT
@payment_bp.route("/payments/<int:id>", methods=['PATCH'])
def update_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    data = request.get_json()
    for key, value in data.items():
        setattr(payment, key, value)
    db.session.commit()

    return jsonify(payment.to_dict()), 200

# ✅ DELETE PAYMENT
@payment_bp.route('/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    db.session.delete(payment)
    db.session.commit()

    return jsonify({"msg": "Payment deleted successfully"}), 200
