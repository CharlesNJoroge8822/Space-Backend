from datetime import datetime
from app import db

class Agreement(db.Model):
    __tablename__ = 'agreements'

    id = db.Column(db.Integer, primary_key=True)
    terms = db.Column(db.Text, nullable=False)
    accepted = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)
