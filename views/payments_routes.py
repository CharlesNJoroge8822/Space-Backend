from flask import Blueprint, request, jsonify
from models import Payment, Booking, db
from datetime import datetime
import uuid
from utils.mpesa_helper import stk_push
import logging

payment_bp = Blueprint("payment_bp", __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # Log the incoming payload
    print("Received STK Push Payload:", data)

    # Ensure required fields exist
    required_fields = ["phone_number", "amount", "order_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    phone_number = data["phone_number"]
    amount = data["amount"]
    order_id = data["order_id"]

    try:
        # Call stk_push function
        response = stk_push(phone_number, amount, order_id)
        return jsonify(response), 200
    except Exception as e:
        print("STK Push Error:", str(e))  # Log the error
        return jsonify({"error": str(e)}), 500

# !M-pesa Callback route
@payment_bp.route('/callback', methods=['POST'])
def handle_callback():
    callback_data = request.json

    # Log the callback data for debugging
    logger.info("Received M-Pesa Callback Data: %s", callback_data)

    # Validate callback data
    if not callback_data or 'Body' not in callback_data or 'stkCallback' not in callback_data['Body']:
        logger.error("Invalid callback data received")
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback data"}), 400

    # Extract relevant data
    stk_callback = callback_data['Body']['stkCallback']
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')  # Use CheckoutRequestID as order_id

    if result_code != 0:
        # If the result code is not 0, there was an error
        error_message = stk_callback.get('ResultDesc', 'Payment failed')
        logger.error(f"Payment failed for order {checkout_request_id}: {error_message}")
        return jsonify({"ResultCode": result_code, "ResultDesc": error_message})

    # If the result code is 0, the transaction was successful
    callback_metadata = stk_callback.get('CallbackMetadata', {})
    amount = None
    phone_number = None

    if 'Item' in callback_metadata:
        for item in callback_metadata['Item']:
            if item.get('Name') == 'Amount':
                amount = item.get('Value')
            elif item.get('Name') == 'PhoneNumber':
                phone_number = item.get('Value')

    # Log successful payment
    logger.info(f"Payment successful for order {checkout_request_id}. Amount: {amount}, Phone: {phone_number}")

    return jsonify({"ResultCode": 0, "ResultDesc": "Payment received successfully"})

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