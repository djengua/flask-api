from app import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120))
    lastname = db.Column(db.String(120))
    role_id = db.Column(db.Integer, db.ForeignKey(
        'roles.id'), nullable=True)  # Relación con Role
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at,
            'active': self.active,
            # 'company_count': self.companies.count(),
            # 'primary_company_id': self.primary_company_id
        }
