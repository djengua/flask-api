from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
import sys

import os
import sys

# Imprimir todas las variables de entorno (ocultando valores sensibles)
print("=== VARIABLES DE ENTORNO DISPONIBLES ===")
for key in os.environ:
    if key in ['DATABASE_URL', 'JWT_SECRET_KEY']:
        print(f"{key}: ***valor oculto***")
    else:
        print(f"{key}: {os.environ[key]}")
print("=======================================")

# Intenta leer la variable DATABASE_URL de múltiples formas
database_url = None

# Inicializar Flask
app = Flask(__name__)

# IMPORTANTE: Railway proporciona la variable DATABASE_URL
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Railway usa postgres:// pero SQLAlchemy necesita postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(
        f"Usando URL de base de datos desde variables de entorno: {database_url}")
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
    print(f"URL manual: {manual_url}")
    app.config['SQLALCHEMY_DATABASE_URI'] = manual_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY', 'super-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

print(f"URL final de base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Inicializar extensiones
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Manejo seguro de inicialización de base de datos
try:
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada correctamente")
except Exception as e:
    print(f"Error al inicializar la base de datos: {str(e)}")


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the User Management API'}), 200

# Ruta para depuración


# @app.route('/debug')
# def debug():
#     config = {
#         'SQLALCHEMY_DATABASE_URI': app.config['SQLALCHEMY_DATABASE_URI'].replace(
#             os.environ.get('DB_PASS', ''), '****') if 'SQLALCHEMY_DATABASE_URI' in app.config else None,
#         'DATABASE_URL_EXISTS': 'DATABASE_URL' in os.environ,
#         'ENV_VARS': [key for key in os.environ.keys()
#                      if not ('password' in key.lower() or 'secret' in key.lower() or 'key' in key.lower())]
#     }

#     # Probar conexión a la base de datos
#     db_status = {}
#     try:
#         result = db.session.execute('SELECT 1').scalar()
#         db_status['connected'] = True
#         db_status['result'] = result
#     except Exception as e:
#         db_status['connected'] = False
#         db_status['error'] = str(e)

#     return jsonify({
#         'app_config': config,
#         'db_status': db_status
#     })
