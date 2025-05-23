from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
from flask_cors import CORS
import os
import sys


from dotenv import load_dotenv
load_dotenv()

database_url = None

# Inicializar Flask
app = Flask(__name__)

CORS(app, resources={r"/api/*": {
    "origins": [
        "https://djengua.com",
        "http://localhost:8081",
        "http://localhost",
        "http://10.3.12.240:8081"
        ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

database_url = os.environ.get('DATABASE_URL')

if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print("Usando URL de base de datos desde variables de entorno: OK")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Configuración manual como respaldo
    print("No se encontró DATABASE_URL, usando configuración manual")
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASS = os.environ.get('DB_PASS', 'postgres')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'user_api')

    manual_url = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print("URL manual: OK")
    app.config['SQLALCHEMY_DATABASE_URI'] = manual_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY', 'super-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

print("URL final de base de datos: OK")

# Inicializar extensiones
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the User Management API'}), 200


@app.route('/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes), 200


def init_db():
    with app.app_context():
        # Importar todos los modelos aquí
        from app.models.roles import Role
        from app.models.users import User
        from app.models.companies import Company

        # Crear todas las tablas
        db.create_all()
        Role.init_roles(db.session)
        print("Base de datos inicializada correctamente")


def register_blueprints():
    from app.routes.auth import auth_bp
    from app.routes.user import users_bp
    from app.routes.companies import companies_bp
    # Si tienes blueprint de usuarios, también lo importarías aquí
    # from app.routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(companies_bp, url_prefix='/api/companies')
