from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models.users import User

users_bp = Blueprint('users', __name__)


@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    print('me')
    user_id = get_jwt_identity()
    print(user_id)
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'lastname': user.lastname,
        'active': user.active
    }), 200

# Obtener todos los usuarios (para administradores)


@users_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()

    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'lastname': user.lastname,
            'active': user.active
        })

    return jsonify(user_list), 200

# Obtener usuario por ID


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'lastname': user.lastname,
        'active': user.active
    }), 200

# Actualizar usuario


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()

    # Solo permitir actualizar el propio usuario o implementar lógica de admin
    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized to modify this user'}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()

    if data.get('name'):
        user.name = data['name']

    if data.get('lastname'):
        user.lastname = data['lastname']

    if data.get('email'):
        # Verificar disponibilidad del nuevo email
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'message': 'Email already registered'}), 409
        user.email = data['email']

    if data.get('password'):
        user.password = bcrypt.generate_password_hash(
            data['password']).decode('utf-8')

    # Guardar cambios
    db.session.commit()

    return jsonify({
        'message': 'User updated successfully',
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'lastname': user.lastname,
        'active': user.active
    }), 200

# Eliminar usuario


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    # Solo permitir eliminar el propio usuario o implementar lógica de admin
    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized to delete this user'}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Eliminar usuario
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200
