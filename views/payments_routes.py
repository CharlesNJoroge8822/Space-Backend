from flask import Blueprint, request, jsonify
from models import Payment, db
from datetime import datetime
import uuid
from utils.mpesa_helper import stk_push

payment_bp = Blueprint("payment_bp", __name__)

#! CREATE PAYMENT
@payment_bp.route("/payments", methods=['POST'])
def create_payment():
    # Generate a unique MPESA transaction ID
    unique_mpesa_id = str(uuid.uuid4())[:10]
    data = request.get_json()

    required_fields = ["booking_id", "user_id", "amount", "phone_number"]  
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_payment = Payment(
        booking_id=data["booking_id"],
        user_id=data["user_id"],
        amount=data["amount"],
        mpesa_transaction_id=unique_mpesa_id,  # Use generated id
        phone_number=data["phone_number"],
        status=data.get("status", "Processing")  # Default status is processing 
    )

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"message": "Payment created successfully", "mpesa_transaction_id": unique_mpesa_id}), 201

# !M-pesa STK push route
@payment_bp.route("/stkpush", methods=["POST"])
def initiate_stk_push():
    data = request.get_json()

    # Ensure required fields exist
    required_fields = ["phone_number", "amount", "order_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    phone_number = data["phone_number"]
    amount = data["amount"]
    order_id = data["order_id"]  # Unique ID for tracking

    # Call stk_push function
    response = stk_push(phone_number, amount, order_id)

    return jsonify(response)

#! FETCH SINGLE PAYMENT
@payment_bp.route("/payments/<int:id>", methods=['GET'])
def fetch_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify(payment.to_dict()), 200


#! FETCH ALL PAYMENTS
@payment_bp.route("/payments", methods=['GET'])
def fetch_all_payments():
    payments = Payment.query.all()
    payments_list = [payment.to_dict() for payment in payments]
    return jsonify({"payments": payments_list}), 200


#! UPDATE PAYMENT
@payment_bp.route("/payments/<int:id>", methods=['PATCH'])
def update_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    data = request.get_json()
    for key, value in data.items():
        if hasattr(payment, key):
            setattr(payment, key, value)
    
    payment.timestamp = datetime.utcnow()  # Update timestamp on edit
    db.session.commit()

    return jsonify(payment.to_dict()), 200


#! DELETE PAYMENT
@payment_bp.route('/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    db.session.delete(payment)
    db.session.commit()

    return jsonify({"message": "Payment deleted successfully"}), 200
