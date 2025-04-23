from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models.companies import Company
from app.models.users import User
from app.models.roles import Role, ROLE_SUPERADMIN
import pytz

mexico_timezone = pytz.timezone('America/Mexico_City')

companies_bp = Blueprint('companies', __name__)

# Obtener todos las compañias (para administradores)
@companies_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_companies():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Verificar que el usuario exista
    if not current_user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    
    # Determinar qué compañías mostrar según el rol
    if current_user.role_id == ROLE_SUPERADMIN:
        # Los superadmins ven todas las compañías
        companies = Company.query.order_by(Company.id).all()
    else:
        # Los usuarios normales y admins solo ven sus compañías asociadas
        companies = current_user.companies.order_by(Company.id).all()
    
    company_list = []
    for company in companies:
        mexico_time = company.created_at.astimezone(mexico_timezone)
        # Obtener información del usuario creador (si existe)
        user_info = None
        if company.user_id:
            creator = User.query.get(company.user_id)
            if creator:
                user_info = {
                    'id': creator.id,
                    'name': f"{creator.name} {creator.lastname}".strip(),
                    'email': creator.email
                }
        
        company_list.append({
            'id': company.id,
            'name': company.name,
            'description': company.description,
            'user': user_info,
            'created_at': mexico_time.isoformat(), # company.created_at,
            'active': company.active
        })

    return jsonify(company_list), 200

@companies_bp.route('', methods=['POST'])
@jwt_required()
def add_company():
    current_user_id = get_jwt_identity()

    # Verificar que el usuario exista y sea superadmin
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    

    # {"name":"powerman","description":"powerman","active":false}
    
    # Obtener el rol del usuario
    role = Role.query.get(current_user.role_id)
    if not role or role.id != ROLE_SUPERADMIN:
        return jsonify({'message': 'No tienes permisos para crear compañías. Solo los superadministradores pueden realizar esta acción.'}), 403
    
    # Obtener datos del JSON
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No se proporcionaron datos'}), 400
    
    # Validar que name exista y no esté vacío
    if not data.get('name'):
        return jsonify({'message': 'El nombre de la compañía es requerido'}), 400
    
    # Validar que description exista y no esté vacío
    if not data.get('description'):
        return jsonify({'message': 'La descripción de la compañía es requerida'}), 400
    
    # Verificar si el nombre de la compañía ya existe
    if Company.query.filter_by(name=data.get('name')).first():
        return jsonify({'message': 'Ya existe una compañía con ese nombre'}), 409
    
    # El usuario de contacto es opcional
    user_id = data.get('user_id')
    user = User.query.get(user_id)
    if user_id and not user: # User.query.get(user_id):
        return jsonify({'message': 'Usuario de contacto no encontrado'}), 404
    
    # Crear una nueva instancia de Company
    company = Company(
        name=data.get('name'),
        description=data.get('description'),
        user_id=user_id,
        active=data.get('active', True)
    )
    
    # Agregar a la sesión y guardar
    db.session.add(company)
    db.session.commit()

    mexico_time = company.created_at.astimezone(mexico_timezone)
    
    # Asociar usuarios si se proporcionan
    if 'user_id' in data and data['user_id']:
        users = User.query.filter(User.id.in_([user_id])).all()
        for user in users:
            user.companies.append(company)
        db.session.commit()

    response_data = {
        'id': company.id,
        'name': company.name,
        'description': company.description,
        'created_at': mexico_time.isoformat(), # company.created_at.isoformat(),
        'active': company.active       
    }

    # Only add user info if a user exists
    if user:
        response_data['user'] = {
            'id': user.id,
            'name': user.name
        }
    else:
        response_data['user'] = None

    return jsonify(response_data), 201

@companies_bp.route('/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company(company_id):
    current_user_id = get_jwt_identity()
    
    # Verificar que el usuario exista y sea superadmin
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    
    # Validar que sea superadmin
    role = Role.query.get(current_user.role_id)
    if not role or role.id != ROLE_SUPERADMIN:
        return jsonify({'message': 'No tienes permisos para editar compañías. Solo los superadministradores pueden realizar esta acción.'}), 403
    
    # Obtener la compañía por ID
    company = Company.query.get(company_id)
    
    if not company:
        return jsonify({'message': 'Compañía no encontrada'}), 404
    
    # Obtener datos del JSON
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No se proporcionaron datos para actualizar'}), 400
    
    # Actualizar campos si se proporcionan
    if 'name' in data and data['name']:
        # Verificar que el nuevo nombre no exista ya (si se está cambiando)
        if data['name'] != company.name and Company.query.filter_by(name=data['name']).first():
            return jsonify({'message': 'Ya existe una compañía con ese nombre'}), 409
        company.name = data['name']
    
    if 'description' in data and data['description']:
        company.description = data['description']
    
    if 'user_id' in data:
        # Verificar que el usuario exista si se proporciona
        if data['user_id'] and not User.query.get(data['user_id']):
            return jsonify({'message': 'Usuario de contacto no encontrado'}), 404
        company.user_id = data['user_id']
    
    if 'active' in data:
        company.active = data['active']

    user_id = data.get('user_id')
    
    if 'user_id' in data and data['user_id']:
        users = User.query.filter(User.id.in_([user_id])).all()
        print(len(users))
        for user in users:
            user.companies.append(company)
        db.session.commit()
    
    # Actualizar usuarios asociados si se proporcionan
    # if 'user_ids' in data:
    #     user_ids = data['user_ids']
        
    #     # Obtener los usuarios actuales
    #     users_to_update = User.query.filter(User.id.in_(user_ids)).all()
    #     found_ids = [user.id for user in users_to_update]
        
    #     # Verificar que todos los IDs proporcionados existan
    #     missing_ids = [id for id in user_ids if id not in found_ids]
    #     if missing_ids:
    #         return jsonify({'message': f'Usuarios no encontrados: {missing_ids}'}), 404
        
    #     # Actualizar la relación (eliminar todos y añadir los nuevos)
    #     for user in User.query.all():
    #         if company in user.companies:
    #             user.companies.remove(company)
        
    #     for user in users_to_update:
    #         user.companies.append(company)
        
    #     # Verificar usuarios con esta compañía como principal
    #     users_with_primary = User.query.filter_by(primary_company_id=company.id).all()
    #     for user in users_with_primary:
    #         if user.id not in user_ids:
    #             # Si el usuario ya no está asociado, eliminar como compañía principal
    #             user.primary_company_id = None
    
    # Guardar cambios
    db.session.commit()

    mexico_time = company.created_at.astimezone(mexico_timezone)

    response_data = {
        'id': company.id,
        'name': company.name,
        'description': company.description,
        'created_at': mexico_time.isoformat(), # company.created_at.isoformat(),
        'active': company.active
    }

    # Only add user info if a user exists
    if user:
        response_data['user'] = {
            'id': user.id,
            'name': user.name
        }
    else:
        response_data['user'] = None

    return jsonify(response_data), 200
    
    # return jsonify({
    #     'message': 'Compañía actualizada exitosamente',
    #     'company': {
    #         'id': company.id,
    #         'name': company.name,
    #         'description': company.description,
    #         'user_id': company.user_id,
    #         'created_at': company.created_at.isoformat(),
    #         'active': company.active
    #     }
    # }), 200
