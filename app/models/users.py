from app import db
from datetime import datetime

user_companies = db.Table('user_companies',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120))
    lastname = db.Column(db.String(120))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    primary_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    primary_company = db.relationship('Company', foreign_keys=[primary_company_id])
    companies = db.relationship('Company', secondary=user_companies, 
                               backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f'<User {self.email} {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'lastname': self.lastname,
            'role_id': self.role_id,
            'role': self.role_obj.to_dict() if hasattr(self, 'role_obj') and self.role_obj else None,
            'created_at': self.created_at,
            'active': self.active,
            'primary_company_id': self.primary_company_id,
            'primary_company': self.primary_company.to_dict() if self.primary_company else None,
            'companies': [company.to_dict() for company in self.companies] if self.companies else []
        }
