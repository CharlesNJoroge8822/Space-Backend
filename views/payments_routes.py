from flask import Blueprint, request, jsonify
from models import Payment, Booking, db, Space, User
from datetime import datetime
import uuid
from utils.mpesa_helper import stk_push
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity

payment_bp = Blueprint("payment_bp", __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! CREATE PAYMENT
@payment_bp.route("/payments", methods=['POST'])
def create_payment():
    unique_mpesa_id = str(uuid.uuid4())[:10]
    data = request.get_json()

    required_fields = ["booking_id", "user_id", "amount", "phone_number"]  
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    new_payment = Payment(
        booking_id=data["booking_id"],
        user_id=data["user_id"],
        amount=data["amount"],
        mpesa_transaction_id=unique_mpesa_id,
        phone_number=data["phone_number"],
        status=data.get("status", "Processing")
    )

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"message": "Payment created successfully", "mpesa_transaction_id": unique_mpesa_id}), 201

# !M-pesa Callback route
@payment_bp.route('/callback', methods=['POST'])
def handle_callback():
    callback_data = request.json
    logger.info("Received M-Pesa Callback Data: %s", callback_data)

    if not callback_data or 'Body' not in callback_data or 'stkCallback' not in callback_data['Body']:
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback data"}), 400

    stk_callback = callback_data['Body']['stkCallback']
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')

    if result_code != 0:
        return jsonify({"ResultCode": result_code, "ResultDesc": "Payment failed"})

    callback_metadata = stk_callback.get('CallbackMetadata', {})
    transaction_id = None
    for item in callback_metadata.get('Item', []):
        if item.get('Name') == 'MpesaReceiptNumber':
            transaction_id = item.get('Value')

    payment = Payment.query.filter_by(mpesa_transaction_id=checkout_request_id).first()
    if not payment:
        return jsonify({"ResultCode": 1, "ResultDesc": "Payment record not found"}), 404

    payment.status = "Confirmed"
    payment.mpesa_transaction_id = transaction_id
    db.session.commit()

    booking = Booking.query.get(payment.booking_id)
    if booking:
        booking.status = "Booked"
        db.session.commit()
        
        space = Space.query.get(booking.space_id)
        if space:
            space.availability = False
            db.session.commit()

    return jsonify({"ResultCode": 0, "ResultDesc": "Payment received, booking confirmed, and space marked as booked."}), 200

#! UPDATE SPACE AVAILABILITY
@payment_bp.route("/spaces/<int:space_id>/availability", methods=['PATCH'])
def update_space_availability(space_id):
    space = Space.query.get(space_id)

    if not space:
        return jsonify({"error": "Space not found"}), 404

    data = request.get_json()
    if "availability" not in data:
        return jsonify({"error": "Missing availability field"}), 400

    active_bookings = Booking.query.filter(
        Booking.space_id == space_id,
        Booking.status.in_(["Booked", "Pending Payment"])
    ).count()

    if data["availability"] and active_bookings > 0:
        return jsonify({"error": "Cannot mark space as available while there are active bookings"}), 400

    space.availability = data["availability"]
    db.session.commit()

    return jsonify({
        "id": space.id,
        "availability": space.availability,
        "message": f"Space status updated to {'Available' if space.availability else 'Booked'}"
}),200