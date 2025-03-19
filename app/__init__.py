from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://username:password@localhost/api')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(
    f"Usando configuración manual de base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}", file=sys.stderr)


# Inicializar extensiones
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Inicializar la base de datos
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the User Management API'}), 200
