from flask import Blueprint, request, jsonify
from models import Agreement, db

agreement_bp = Blueprint("agreement_bp", __name__)

# Create Agreement
@agreement_bp.route("/agreements", methods=['POST'])
def create_agreement():
    data = request.get_json()

    user_id = data.get('user_id')
    space_id = data.get('space_id')
    terms = data.get('terms')

    new_agreement = Agreement(user_id=user_id, space_id=space_id, terms=terms)

    db.session.add(new_agreement)
    db.session.commit()

    return jsonify({
        "id": new_agreement.id,
        "user_id": new_agreement.user_id,
        "space_id": new_agreement.space_id,
        "terms": new_agreement.terms
    }), 201

# Fetch Agreement by ID
@agreement_bp.route("/agreements/<int:id>", methods=['GET'])
def fetch_agreement(id):
    agreement = Agreement.query.get(id)

    if agreement is None:
        return jsonify({"error": "Agreement not found"}), 404

    return jsonify({
        "id": agreement.id,
        "user_id": agreement.user_id,
        "space_id": agreement.space_id,
        "terms": agreement.terms
    })

# Update Agreement
@agreement_bp.route("/agreements/<int:id>", methods=['PATCH'])
def update_agreement(id):
    agreement = Agreement.query.get(id)

    if agreement is None:
        return jsonify({"error": "Agreement not found"}), 404

    data = request.get_json()

    terms = data.get('terms')

    if terms:
        agreement.terms = terms

    db.session.commit()

    return jsonify({
        "id": agreement.id,
        "user_id": agreement.user_id,
        "space_id": agreement.space_id,
        "terms": agreement.terms
    }), 200

# Delete Agreement
@agreement_bp.route('/agreements/<int:id>', methods=['DELETE'])
def delete_agreement(id):
    agreement = Agreement.query.get(id)

    if agreement is None:
        return jsonify({"error": "Agreement not found"}), 404

    db.session.delete(agreement)
    db.session.commit()

    return jsonify({"msg": "Agreement deleted successfully"}), 200
