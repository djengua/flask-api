from app import db
from datetime import datetime


class Company(db.Model):

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'active': self.active
        }


    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(355))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Relación con el usuario creador (opcional)
    contact_user = db.relationship('User', foreign_keys=[user_id], backref='contact_for_companies')

    def __repr__(self):
        return f'<Company {self.name}>'

    def to_dict(self):
        # Datos básicos de la compañía
        company_dict = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'active': self.active
        }
        
        if self.user_id and hasattr(self, 'contact_user') and self.contact_user:
            company_dict['user'] = {
                'id': self.contact_user.id,
                'name': self.contact_user.name,
                'email': self.contact_user.email
            }
        else:
            company_dict['user'] = None
        
        return company_dict