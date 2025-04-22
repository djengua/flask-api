from flask import request, jsonify, Blueprint
from flask_jwt_extended import create_access_token
from app import bcrypt, db
from app.models.users import User
from app.models.roles import ROLE_USER

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validar datos requeridos
    if not data:
        return jsonify({'message': 'No se proporcionaron datos'}), 400
    
    # Verificar campos obligatorios
    required_fields = ['email', 'password', 'name', 'lastname']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            'message': 'Faltan campos requeridos', 
            'missing_fields': missing_fields
        }), 400

    # Verificar si el correo ya está registrado
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'El correo electrónico ya está registrado'}), 409

    # Crear nuevo usuario
    hashed_password = bcrypt.generate_password_hash(
        data['password']).decode('utf-8')
    new_user = User(
        name=data['name'],
        lastname=data['lastname'],
        email=data['email'],
        password=hashed_password,
        role_id=ROLE_USER
    )

    # Guardar en la base de datos
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente', 'user_id': new_user.id}), 201


# Login de usuario
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validar datos requeridos
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    # Buscar usuario
    user = User.query.filter_by(email=data['email']).first()

    print('login')
    print(data)

    print(user)

    # Verificar credenciales
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Generar token JWT
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401
