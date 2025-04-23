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
    """
    Obtiene el usuario actual basado en el token JWT.
    Incluye información de relaciones (rol y compañías)
    """
    current_user_id = get_jwt_identity()
    # Cargamos el usuario con todas sus relaciones en una sola consulta (eager loading)
    user = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).filter_by(id=current_user_id).first()
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Utilizamos el método to_dict actualizado que ya incluye las relaciones
    return jsonify(user.to_dict()), 200


# Obtener todos los usuarios (para administradores)
@users_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Obtiene todos los usuarios con sus relaciones.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar que sea superadmin o admin
    if not current_user or current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para ver todos los usuarios'}), 403
    
    # Cargamos todos los usuarios con sus relaciones en una sola consulta
    users = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).all()
    
    # Usamos el método to_dict actualizado para cada usuario
    return jsonify([user.to_dict() for user in users]), 200


# Obtener usuario por ID
@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Obtiene un usuario específico por su ID con todas sus relaciones.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar permisos: solo el propio usuario o admin/superadmin pueden ver detalles
    if current_user_id != user_id and current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para ver este usuario'}), 403
    
    # Cargamos el usuario con todas sus relaciones
    user = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).filter_by(id=user_id).first()
    
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Utilizamos el método to_dict actualizado
    return jsonify(user.to_dict()), 200


# Actualizar usuario
@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id, data):
    """
    Actualiza un usuario existente.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar permisos: solo el propio usuario o admin/superadmin pueden actualizar
    if current_user_id != user_id and current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para actualizar este usuario'}), 403
    
    # Obtener datos de la solicitud
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Restricciones adicionales para usuarios normales
    if current_user.role_id == ROLE_USER and current_user_id == user_id:
        # Usuarios normales no pueden cambiar su propio rol
        if 'role_id' in data:
            return jsonify({"error": "No tienes permisos para cambiar tu rol"}), 403
    
    # Actualizar campos
    if 'email' in data:
        # Verificar que el nuevo email no exista ya (si se está cambiando)
        if data['email'] != user.email and User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "El email ya está registrado"}), 400
        user.email = data['email']
    
    if 'name' in data:
        user.name = data['name']
    
    if 'lastname' in data:
        user.lastname = data['lastname']
    
    # Solo admin/superadmin pueden cambiar roles
    if 'role_id' in data and current_user.role_id in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        # Admins no pueden crear superadmins
        if current_user.role_id == ROLE_ADMIN and int(data['role_id']) == ROLE_SUPERADMIN:
            return jsonify({"error": "Los administradores no pueden asignar rol de superadmin"}), 403
        user.role_id = data['role_id']
    
    if 'active' in data and current_user.role_id in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        user.active = data['active']
    
    if 'primary_company_id' in data:
        # Verificar que la compañía exista
        if not Company.query.get(data['primary_company_id']):
            return jsonify({"error": "Compañía principal no encontrada"}), 404
        
        # Verificar que el usuario esté asociado a esta compañía
        user_company_ids = [c.id for c in user.companies]
        if data['primary_company_id'] not in user_company_ids:
            return jsonify({"error": "La compañía principal debe ser una de las compañías asociadas al usuario"}), 400
        
        user.primary_company_id = data['primary_company_id']
    
    # Actualizar compañías asociadas (solo admin/superadmin)
    if 'companies' in data and current_user.role_id in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        # Verificar que todas las compañías existan
        company_ids = data['companies']
        if company_ids:
            companies = Company.query.filter(Company.id.in_(company_ids)).all()
            # Verificar que se encontraron todas las compañías solicitadas
            if len(companies) != len(company_ids):
                return jsonify({"error": "Una o más compañías no fueron encontradas"}), 404
            
            # Si es admin, solo puede asignar compañías a las que tiene acceso
            if current_user.role_id == ROLE_ADMIN:
                admin_company_ids = [c.id for c in current_user.companies]
                for company_id in company_ids:
                    if company_id not in admin_company_ids:
                        return jsonify({"error": f"No tienes acceso a la compañía {company_id}"}), 403
            
            # Limpiar asociaciones existentes y agregar las nuevas
            user.companies = []
            user.companies.extend(companies)
            
            # Verificar que la compañía principal siga siendo válida
            if user.primary_company_id and user.primary_company_id not in company_ids:
                # Si la compañía principal ya no está en la lista, seleccionar la primera
                user.primary_company_id = company_ids[0] if company_ids else None
    
    # Si se proporciona contraseña, actualizarla
    if 'password' in data and data['password']:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user.password = hashed_password
    
    db.session.commit()
    
    # Recargar el usuario con todas sus relaciones
    updated_user = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).filter_by(id=user_id).first()
    
    return jsonify(updated_user.to_dict()), 200


# Eliminar usuario
@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """
    Elimina un usuario (desactivación lógica).
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Solo admin/superadmin pueden desactivar usuarios
    if current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para desactivar usuarios'}), 403
    
    # No se puede desactivar a uno mismo
    if current_user_id == user_id:
        return jsonify({'message': 'No puedes desactivar tu propia cuenta'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # No se puede desactivar un superadmin siendo admin
    if current_user.role_id == ROLE_ADMIN and user.role_id == ROLE_SUPERADMIN:
        return jsonify({'message': 'No tienes permisos para desactivar a un superadministrador'}), 403
    
    # Desactivación lógica en lugar de eliminación física
    user.active = False
    db.session.commit()
    
    return jsonify({"message": "Usuario desactivado correctamente"}), 200

# Crear usuarios nuevos como superadmin y admin
@users_bp.route('/create', methods=['POST'])
@jwt_required()
def create_user(data):
    """
    Crea un nuevo usuario.
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar que sea superadmin o admin
    if not current_user or current_user.role_id not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        return jsonify({'message': 'No tienes permisos para crear usuarios'}), 403
    
    data = request.get_json()
    
    # Validar datos requeridos
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Faltan campos requeridos (email y password)'}), 400
    
    # Verificar si el email ya existe
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"error": "El email ya está registrado"}), 400
    
    # Validar rol solicitado
    role_id = data.get('role_id', ROLE_USER)
    
    # Restricciones según rol del creador
    if current_user.role_id == ROLE_ADMIN:
        # Los admin pueden crear usuarios y otros admin, pero no superadmin
        if int(role_id) == ROLE_SUPERADMIN:
            return jsonify({'message': 'Los administradores no pueden crear superadmins'}), 403
    
    # Verificar compañías asociadas
    company_ids = data.get('companies', [])
    primary_company_id = data.get('primary_company_id')
    
    # Si es admin, solo puede asignar compañías a las que tiene acceso
    if current_user.role_id == ROLE_ADMIN and company_ids:
        admin_company_ids = [c.id for c in current_user.companies]
        for company_id in company_ids:
            if company_id not in admin_company_ids:
                return jsonify({
                    'message': f'No tienes acceso a la compañía con ID {company_id}'
                }), 403
    
    # Verificar que la compañía principal sea parte de las compañías asociadas
    if primary_company_id and company_ids and primary_company_id not in company_ids:
        return jsonify({'message': 'La compañía principal debe ser una de las compañías asociadas'}), 400
    
    # Crear el nuevo usuario
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        email=data.get('email'),
        password=hashed_password,
        name=data.get('name', ''),
        lastname=data.get('lastname', ''),
        role_id=role_id,
        primary_company_id=primary_company_id
    )
    
    # Agregar compañías asociadas si se proporcionan
    if company_ids:
        companies = Company.query.filter(Company.id.in_(company_ids)).all()
        new_user.companies.extend(companies)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Cargar el usuario recién creado con todas sus relaciones
    created_user = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).filter_by(id=new_user.id).first()
    
    return jsonify(created_user.to_dict()), 201


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
    
    # Recargar el usuario con todas sus relaciones
    updated_user = User.query.options(
        db.joinedload(User.role_obj),
        db.joinedload(User.primary_company),
        db.joinedload(User.companies)
    ).filter_by(id=current_user_id).first()
    
    return jsonify({
        'message': 'Compañía principal actualizada correctamente',
        'user': updated_user.to_dict()
    }), 200
