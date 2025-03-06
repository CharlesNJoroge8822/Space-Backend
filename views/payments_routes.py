from flask import Blueprint, request, jsonify
from models import Payment, Booking, db, Space
from datetime import datetime
import uuid
from utils.mpesa_helper import stk_push
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

payment_bp = Blueprint("payment_bp", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! ✅ CREATE PAYMENT
@payment_bp.route("/payments", methods=['POST'])
def create_payment():
    try:
        data = request.get_json()

        required_fields = ["booking_id", "user_id", "amount", "phone_number"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        new_payment = Payment(
            booking_id=data["booking_id"],
            user_id=data["user_id"],
            amount=data["amount"],
            mpesa_transaction_id=str(uuid.uuid4())[:10],  # Generate unique ID
            phone_number=data["phone_number"],
            status="Processing"  # Default status
        )

        db.session.add(new_payment)
        db.session.commit()

        return jsonify({
            "message": "Payment created successfully",
            "data": new_payment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error creating payment: {e}")
        return jsonify({"error": "An error occurred while creating the payment"}), 500


#! ✅ INITIATE STK PUSH
@payment_bp.route("/stkpush", methods=["POST"])
def initiate_stk_push():
    try:
        data = request.get_json()
        logger.info("Received STK Push Payload: %s", data)

        required_fields = ["phone_number", "amount", "order_id"]
        if not all(field in data for field in required_fields):
            logger.error("❌ Missing required fields in STK push request")
            return jsonify({"error": "Missing required fields"}), 400

        response = stk_push(data["phone_number"], data["amount"], data["order_id"])
        logger.info("✅ STK Push Response: %s", response)

        if "mpesa_transaction_id" not in response or not response["mpesa_transaction_id"]:
            logger.error("❌ STK Push Response missing transaction ID: %s", response)
            return jsonify({"error": "Invalid STK Push response. No transaction ID received."}), 500

        return jsonify({
            "message": "STK Push initiated successfully",
            "data": response
        }), 200

    except Exception as e:
        logger.error("❌ STK Push Error: %s", str(e))
        return jsonify({"error": str(e)}), 500


#! ✅ HANDLE MPESA CALLBACK
@payment_bp.route('/callback', methods=['POST'])
def handle_callback():
    try:
        callback_data = request.json
        logger.info("Received M-Pesa Callback Data: %s", callback_data)

        if not callback_data or 'Body' not in callback_data or 'stkCallback' not in callback_data['Body']:
            logger.error("Invalid callback data received")
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback data"}), 400

        stk_callback = callback_data['Body']['stkCallback']
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        if result_code != 0:
            error_message = stk_callback.get('ResultDesc', 'Payment failed')
            logger.error(f"Payment failed for order {checkout_request_id}: {error_message}")
            return jsonify({"ResultCode": result_code, "ResultDesc": error_message})

        callback_metadata = stk_callback.get('CallbackMetadata', {})
        amount = None
        phone_number = None

        if 'Item' in callback_metadata:
            for item in callback_metadata['Item']:
                if item.get('Name') == 'Amount':
                    amount = item.get('Value')
                elif item.get('Name') == 'PhoneNumber':
                    phone_number = item.get('Value')

        logger.info(f"✅ Payment successful for order {checkout_request_id}. Amount: {amount}, Phone: {phone_number}")

        payment = Payment.query.filter_by(mpesa_transaction_id=checkout_request_id).first()
        if not payment:
            logger.error(f"🚨 No payment found with transaction ID {checkout_request_id}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Payment record not found"}), 404

        payment.status = "Confirmed"
        db.session.commit()

        booking = Booking.query.get(payment.booking_id)
        if booking:
            booking.status = "Confirmed"
            db.session.commit()
            logger.info(f"✅ Booking ID {booking.id} marked as Confirmed!")

            space = Space.query.get(booking.space_id)
            if space:
                space.status = "Booked"
                db.session.commit()
                logger.info(f"🚀 Space ID {space.id} marked as Booked!")

        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Payment received, booking confirmed, and space marked as booked."
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error handling M-Pesa callback: {e}")
        return jsonify({"error": "An error occurred while processing the callback"}), 500


#! ✅ FETCH SINGLE PAYMENT
@payment_bp.route("/payments/<int:payment_id>", methods=['GET'])
def fetch_payment(payment_id):
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        return jsonify({
            "message": "Payment fetched successfully",
            "data": payment.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching payment with ID {payment_id}: {e}")
        return jsonify({"error": "An error occurred while fetching the payment"}), 500


#! ✅ FETCH ALL PAYMENTS
@payment_bp.route("/payments", methods=['GET'])
def fetch_all_payments():
    try:
        payments = Payment.query.all()
        payments_list = [payment.to_dict() for payment in payments]

        return jsonify({
            "message": "Payments fetched successfully",
            "data": payments_list
        }), 200

    except Exception as e:
        logger.error(f"🚨 Error fetching all payments: {e}")
        return jsonify({"error": "An error occurred while fetching payments"}), 500


#! ✅ UPDATE PAYMENT
@payment_bp.route("/payments/<int:payment_id>", methods=['PATCH'])
def update_payment(payment_id):
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        data = request.get_json()
        for key, value in data.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        payment.timestamp = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Payment updated successfully",
            "data": payment.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error updating payment with ID {payment_id}: {e}")
        return jsonify({"error": "An error occurred while updating the payment"}), 500


#! ✅ DELETE PAYMENT
@payment_bp.route('/payments/<int:payment_id>', methods=['DELETE'])
@jwt_required()
def delete_payment(payment_id):
    try:
        current_user_id = get_jwt_identity()
        payment = Payment.query.get(payment_id)

        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        if payment.user_id != current_user_id and User.query.get(current_user_id).role != "Admin":
            return jsonify({"error": "Unauthorized to delete this payment"}), 403

        db.session.delete(payment)
        db.session.commit()

        return jsonify({"message": "Payment deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"🚨 Error deleting payment with ID {payment_id}: {e}")
        return jsonify({"error": "An error occurred while deleting the payment"}), 500