from app import db
from datetime import datetime

ROLE_SUPERADMIN = 1
ROLE_ADMIN = 2
ROLE_USER = 3

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    # permissions = db.Column(db.JSON)  # Permisos como un objeto JSON

    users = db.relationship('User', backref='role_obj', lazy=True)

    @staticmethod
    def init_roles(db_session):
        """Inicializa los roles básicos si no existen"""
        roles = {
            ROLE_SUPERADMIN: 'superadmin',
            ROLE_ADMIN: 'admin',
            ROLE_USER: 'user'
        }
        
        for role_id, role_name in roles.items():
            if not Role.query.get(role_id):
                role = Role(id=role_id, name=role_name)
                db_session.add(role)
        
        db_session.commit()