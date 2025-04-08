from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models.users import User
from app.models.companies import Company
from app.models.roles import Role, ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_USER

users_bp = Blueprint('users', __name__)


@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
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
    print(users)

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
    if int(current_user_id) != user_id:
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

# Crear usuarios nuevos como superadmin y admin
@users_bp.route('/create', methods=['POST'])
@jwt_required()
def create_user():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar que sea superadmin o admin
    if not current_user or current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para crear usuarios'}), 403
    
    data = request.get_json()
    
    # Validar datos requeridos
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Faltan campos requeridos'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'El email ya está registrado'}), 409
    
    # Verificar rol solicitado
    role_id = data.get('role_id', ROLE_USER)
    
    # Restricciones según rol del creador
    if current_user.role_id == ROLE_ADMIN:
        # Los admin pueden crear usuarios y otros admin, pero no superadmin
        if role_id == ROLE_SUPERADMIN:
            return jsonify({'message': 'Los administradores no pueden crear superadmins'}), 403
    
    # Validar que el rol solicitado exista
    if not Role.query.get(role_id):
        return jsonify({'message': 'El rol especificado no existe'}), 400
    
    # Verificar compañías asociadas (opcional)
    company_ids = data.get('company_ids', [])
    primary_company_id = data.get('primary_company_id')

    # Si es admin, solo puede asignar compañías a las que tiene acceso
    if current_user.role_id == ROLE_ADMIN and company_ids:
        admin_company_ids = [company.id for company in current_user.companies]
        
        # Verificar que todas las compañías que se intentan asignar pertenecen al admin
        for company_id in company_ids:
            if company_id not in admin_company_ids:
                return jsonify({
                    'message': f'No tienes acceso a la compañía con ID {company_id}. Solo puedes asignar compañías a las que tienes acceso.'
                }), 403
    
    # Verificar compañías si se proporcionan
    if company_ids:
        # Verificar que todas las compañías existan
        for company_id in company_ids:
            if not Company.query.get(company_id):
                return jsonify({'message': f'Compañía con ID {company_id} no encontrada'}), 404
            
    # Verificar que la compañía principal sea parte de las compañías asociadas
    if primary_company_id:
        if not Company.query.get(primary_company_id):
            return jsonify({'message': 'Compañía principal no encontrada'}), 404
        
        if company_ids and primary_company_id not in company_ids:
            return jsonify({'message': 'La compañía principal debe ser una de las compañías asociadas'}), 400
        
        # Si es admin, verificar que tiene acceso a la compañía principal
        if current_user.role_id == ROLE_ADMIN:
            admin_company_ids = [company.id for company in current_user.companies]
            if primary_company_id not in admin_company_ids:
                return jsonify({
                    'message': 'No tienes acceso a la compañía principal seleccionada'
                }), 403

    # Crear nuevo usuario
    hashed_password = bcrypt.generate_password_hash(
        data['password']).decode('utf-8')
    new_user = User(
        name=data.get('name', ''),
        lastname=data.get('lastname', ''),
        email=data['email'],
        password=hashed_password,
        role_id=role_id,
        primary_company_id=primary_company_id
    )

    # Guardar en la base de datos
    db.session.add(new_user)
    db.session.commit()
    
    # Asociar compañías al usuario (opcional)
    if company_ids:
        companies = Company.query.filter(Company.id.in_(company_ids)).all()
        for company in companies:
            new_user.companies.append(company)
        db.session.commit()
    
    # Obtener información del rol
    role_name = "desconocido"
    role = Role.query.get(role_id)
    if role:
        role_name = role.name
    
    # Obtener información de compañía principal si existe
    primary_company = None
    if primary_company_id:
        company = Company.query.get(primary_company_id)
        if company:
            primary_company = {
                'id': company.id,
                'name': company.name
            }
    
    return jsonify({
        'message': 'Usuario creado exitosamente',
        'user': {
            'id': new_user.id,
            'email': new_user.email,
            'name': new_user.name,
            'lastname': new_user.lastname,
            'role': {
                'id': role_id,
                'name': role_name
            },
            'primary_company': primary_company,
            'company_count': len(new_user.companies) if hasattr(new_user, 'companies') else 0
        }
    }), 201

@users_bp.route('/primary-company', methods=['PUT'])
@jwt_required()
def update_my_primary_company():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar que el usuario exista
    if not current_user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    
    # Obtener datos del JSON
    data = request.get_json()
    if not data or 'primary_company_id' not in data:
        return jsonify({'message': 'Se requiere el ID de la compañía principal'}), 400
    
    primary_company_id = data['primary_company_id']
    
    # Validar que el valor no sea null
    if primary_company_id is None:
        return jsonify({'message': 'El ID de la compañía principal es requerido y no puede ser null'}), 400
    
    # Verificar que la compañía exista
    company = Company.query.get(primary_company_id)
    if not company:
        return jsonify({'message': 'Compañía no encontrada'}), 404
    
    # Verificar que el usuario esté asociado a esta compañía
    user_company_ids = [c.id for c in current_user.companies]
    if primary_company_id not in user_company_ids:
        return jsonify({
            'message': 'La compañía seleccionada no está asociada a tu usuario. Solo puedes seleccionar una compañía asociada como principal.',
            'available_companies': [
                {'id': c.id, 'name': c.name} for c in current_user.companies
            ]
        }), 400
    
    # Actualizar la compañía principal
    current_user.primary_company_id = primary_company_id
    db.session.commit()
    
    # Obtener detalles de la compañía principal para la respuesta
    primary_company = {
        'id': company.id,
        'name': company.name,
        'description': company.description
    }
    
    return jsonify({
        'message': 'Compañía principal actualizada correctamente',
        'primary_company': primary_company
    }), 200
