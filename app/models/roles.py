from app import db
from datetime import datetime


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    # permissions = db.Column(db.JSON)  # Permisos como un objeto JSON

    users = db.relationship('User', backref='role_obj', lazy=True)
