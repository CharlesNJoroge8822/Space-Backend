from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'  # ✅ Ensured table name is correct

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)  # JWT ID (jti)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TokenBlocklist id={self.id}, jti={self.jti}, created_at={self.created_at}>"
