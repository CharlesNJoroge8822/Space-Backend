from flask import Blueprint, request, jsonify
from models import Payment, db

payment_bp = Blueprint("payment_bp", __name__)

# Create Payment
@payment_bp.route("/payments", methods=['POST'])
def create_payment():
    data = request.get_json()

    user_id = data.get('user_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')

    new_payment = Payment(user_id=user_id, amount=amount, payment_method=payment_method)

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        "id": new_payment.id,
        "user_id": new_payment.user_id,
        "amount": new_payment.amount,
        "payment_method": new_payment.payment_method
    }), 201

# Fetch Payment by ID
@payment_bp.route("/payments/<int:id>", methods=['GET'])
def fetch_payment(id):
    payment = Payment.query.get(id)

    if payment is None:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify({
        "id": payment.id,
        "user_id": payment.user_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method
    })

# Update Payment
@payment_bp.route("/payments/<int:id>", methods=['PATCH'])
def update_payment(id):
    payment = Payment.query.get(id)

    if payment is None:
        return jsonify({"error": "Payment not found"}), 404

    data = request.get_json()

    amount = data.get('amount')
    payment_method = data.get('payment_method')

    if amount:
        payment.amount = amount
    if payment_method:
        payment.payment_method = payment_method

    db.session.commit()

    return jsonify({
        "id": payment.id,
        "user_id": payment.user_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method
    }), 200

# Delete Payment
@payment_bp.route('/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    payment = Payment.query.get(id)

    if payment is None:
        return jsonify({"error": "Payment not found"}), 404

    db.session.delete(payment)
    db.session.commit()

    return jsonify({"msg": "Payment deleted successfully"}),200