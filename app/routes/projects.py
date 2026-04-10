from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.project import ProjectModel
from app.models import UserModel

projects_bp = Blueprint('projects', __name__)


# ── GET /api/projects ─────────────────────────────────────────────────────────
@projects_bp.route('/api/projects', methods=['GET'])
def get_projects():
    page     = request.args.get('page',     1,    type=int)
    limit    = request.args.get('limit',    10,   type=int)
    status   = request.args.get('status',   None)
    category = request.args.get('category', None)
    skill    = request.args.get('skill',    None)

    if status and status not in ProjectModel.VALID_STATUSES:
        return jsonify({'message': f'Invalid status. Must be one of: {", ".join(ProjectModel.VALID_STATUSES)}'}), 422

    result = ProjectModel.find_all(page=page, limit=limit, status=status, category=category, skill=skill)
    return jsonify(result), 200


# ── GET /api/projects/my ──────────────────────────────────────────────────────
#client: ses projets
#freelancer: projets disponibles (status pending par défaut)
@projects_bp.route('/api/projects/my', methods=['GET'])
@jwt_required()
def get_my_projects():
    """Récupère les projets de l'utilisateur connecté selon son rôle"""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.get('role') == 'client':
        # Propriétaire de projet : récupère ses propres projets
        result = ProjectModel.find_by_client(user_id)
    else:
        # Freelancer : récupère tous les projets disponibles (pour postuler)
        page     = request.args.get('page',     1,    type=int)
        limit    = request.args.get('limit',    10,   type=int)
        status   = request.args.get('status',   'pending')  # Par défaut pending pour freelancers
        category = request.args.get('category', None)
        skill    = request.args.get('skill',    None)

        result = ProjectModel.find_all(page=page, limit=limit, status=status, category=category, skill=skill)

    return jsonify(result), 200


# ── GET /api/projects/search ──────────────────────────────────────────────────
@projects_bp.route('/api/projects/search', methods=['GET'])
def search_projects():
    q     = request.args.get('q', '')
    page  = request.args.get('page',  1,  type=int)
    limit = request.args.get('limit', 10, type=int)

    result = ProjectModel.search(q=q, page=page, limit=limit)
    return jsonify(result), 200


# ── GET /api/projects/client/<client_id> ──────────────────────────────────────
@projects_bp.route('/api/projects/client/<string:client_id>', methods=['GET'])
@jwt_required()
def get_client_projects(client_id):
    # Vérifier que l'utilisateur peut voir ces projets
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Seuls les clients peuvent voir leurs propres projets, ou les admins
    if user.get('role') != 'client' and str(user_id) != client_id:
        return jsonify({'message': 'Access denied'}), 403

    result = ProjectModel.find_by_client(client_id)
    return jsonify(result), 200


# ── GET /api/projects/<project_id> ────────────────────────────────────────────────────
@projects_bp.route('/api/projects/<string:project_id>', methods=['GET'])
def get_project(project_id):
    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404
    return jsonify(ProjectModel.serialize(project)), 200


# ── POST /api/projects ────────────────────────────────────────────────────────
@projects_bp.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Créer un nouveau projet - réservé aux clients/propriétaires"""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Vérifier que l'utilisateur est un client/propriétaire de projet
    if user.get('role') != 'client':
        return jsonify({'message': 'Only clients can create projects'}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'No JSON body provided'}), 400

    required = ['title', 'budget']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'message': f'Missing fields: {", ".join(missing)}'}), 422

    try:
        float(data.get('budget', 0))
    except (TypeError, ValueError):
        return jsonify({'message': 'Invalid budget value'}), 422

    payload = dict(data)
    payload['client'] = user.get('name', '')
    payload.setdefault('clientAvatar', user.get('avatar', ''))

    # Utiliser l'ID de l'utilisateur connecté comme client_id
    project_id = ProjectModel.create(payload, user_id)
    project    = ProjectModel.find_by_id(project_id)

    if not project:
        return jsonify({'message': 'Failed to create project'}), 500

    return jsonify({
        'message': 'Project created successfully',
        'project': ProjectModel.serialize(project),
    }), 201


# ── PUT /api/projects/<project_id> ────────────────────────────────────────────────────
@projects_bp.route('/api/projects/<string:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Mettre à jour un projet - réservé au propriétaire du projet"""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    # Vérifier que l'utilisateur est le propriétaire du projet
    if project.get('client_id') != user_id:
        return jsonify({'message': 'Access denied: You can only update your own projects'}), 403

    data = request.get_json(silent=True) or {}
    ProjectModel.update(project_id, data)
    return jsonify({'message': 'Project updated successfully'}), 200


# ── PATCH /api/projects/<project_id>/status ───────────────────────────────────────────
#changement de statut avec validation
@projects_bp.route('/api/projects/<string:project_id>/status', methods=['PATCH'])
@jwt_required()
def update_project_status(project_id):
    """Mettre à jour le statut d'un projet - réservé au propriétaire"""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    # Vérifier que l'utilisateur est le propriétaire du projet
    if project.get('client_id') != user_id:
        return jsonify({'message': 'Access denied: You can only update your own projects'}), 403

    data   = request.get_json(silent=True) or {}
    status = data.get('status')

    if not status or status not in ProjectModel.VALID_STATUSES:
        return jsonify({'message': f'Invalid status. Must be one of: {", ".join(ProjectModel.VALID_STATUSES)}'}), 422

    ProjectModel.update_status(project_id, status)
    return jsonify({'message': 'Project status updated successfully'}), 200


# ── DELETE /api/projects/<project_id> ─────────────────────────────────────────────────
@projects_bp.route('/api/projects/<string:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Supprimer un projet - réservé au propriétaire"""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    # Vérifier que l'utilisateur est le propriétaire du projet
    if project.get('client_id') != user_id:
        return jsonify({'message': 'Access denied: You can only delete your own projects'}), 403

    ProjectModel.delete(project_id)
    return jsonify({'message': 'Project deleted successfully'}), 200