from flask import request, jsonify, Blueprint
from flask_jwt_extended import create_access_token
from app import bcrypt, db
from app.models.users import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    print(data)

    # Validar datos requeridos

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409

    # Crear nuevo usuario
    hashed_password = bcrypt.generate_password_hash(
        data['password']).decode('utf-8')
    new_user = User(
        name=data['name'],
        lastname=data['lastname'],
        email=data['email'],
        password=hashed_password,
        role_id=3
    )

    # Guardar en la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Login de usuario


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validar datos requeridos
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    # Buscar usuario
    user = User.query.filter_by(email=data['email']).first()

    # Verificar credenciales
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Generar token JWT
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401
