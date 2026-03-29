from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.projects import ProjectModel
from app.models.proposals import ProposalModel

proposals_bp = Blueprint('proposals', __name__)


# ── GET /api/proposals/<project_id> ───────────────────────────────────────────
@proposals_bp.route('/api/proposals/<string:project_id>', methods=['GET'])
def get_proposals(project_id):
    project = ProjectModel.find_by_id(project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    page  = request.args.get('page',  1,  type=int)
    limit = request.args.get('limit', 10, type=int)

    result = ProposalModel.find_by_project(project_id, page=page, limit=limit)
    return jsonify(result), 200


# ── GET /api/proposals/detail/<proposal_id> ───────────────────────────────────
@proposals_bp.route('/api/proposals/detail/<string:proposal_id>', methods=['GET'])
@jwt_required()
def get_proposal(proposal_id):
    proposal = ProposalModel.find_by_id(proposal_id)
    if not proposal:
        return jsonify({'message': 'Proposal not found'}), 404
    return jsonify(ProposalModel.serialize(proposal)), 200


# ── POST /api/proposals ───────────────────────────────────────────────────────
@proposals_bp.route('/api/proposals', methods=['POST'])
# @jwt_required()  # ← COMMENTÉ POUR TESTER - À RÉACTIVER PLUS TARD!
def create_proposal():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'No JSON body provided'}), 400

    required = ['projectId', 'bidAmount']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'message': f'Missing fields: {", ".join(missing)}'}), 422

    project = ProjectModel.find_by_id(data['projectId'])
    if not project:
        return jsonify({'message': 'Project not found'}), 404

    # Utiliser un freelancer_id par défaut pour les tests
    freelancer_id = 'test_freelancer_123'  # ← TEMPORAIRE
    proposal_id   = ProposalModel.create(data, freelancer_id)

    # Increment proposals counter on the project
    ProjectModel.increment_proposals(data['projectId'], delta=1)

    proposal = ProposalModel.find_by_id(proposal_id)
    return jsonify({
        'message':  'Proposal submitted successfully',
        'proposal': ProposalModel.serialize(proposal),
    }), 201


# ── PUT /api/proposals/<proposal_id> ──────────────────────────────────────────
@proposals_bp.route('/api/proposals/<string:proposal_id>', methods=['PUT'])
@jwt_required()
def update_proposal(proposal_id):
    proposal = ProposalModel.find_by_id(proposal_id)
    if not proposal:
        return jsonify({'message': 'Proposal not found'}), 404

    data = request.get_json(silent=True) or {}
    ProposalModel.update(proposal_id, data)
    return jsonify({'message': 'Proposal updated successfully'}), 200


# ── PATCH /api/proposals/<proposal_id>/status ─────────────────────────────────
@proposals_bp.route('/api/proposals/<string:proposal_id>/status', methods=['PATCH'])
@jwt_required()
def update_proposal_status(proposal_id):
    proposal = ProposalModel.find_by_id(proposal_id)
    if not proposal:
        return jsonify({'message': 'Proposal not found'}), 404

    data   = request.get_json(silent=True) or {}
    status = data.get('status')

    if not status or status not in ProposalModel.VALID_STATUSES:
        return jsonify({'message': f'Invalid status. Must be one of: {", ".join(ProposalModel.VALID_STATUSES)}'}), 422

    ProposalModel.update_status(proposal_id, status)
    return jsonify({'message': 'Proposal status updated successfully'}), 200


# ── DELETE /api/proposals/<proposal_id> ───────────────────────────────────────
@proposals_bp.route('/api/proposals/<string:proposal_id>', methods=['DELETE'])
@jwt_required()
def delete_proposal(proposal_id):
    deleted, project_id = ProposalModel.delete(proposal_id)
    if not deleted:
        return jsonify({'message': 'Proposal not found'}), 404

    # Decrement proposals counter on the project
    if project_id:
        ProjectModel.increment_proposals(project_id, delta=-1)

    return jsonify({'message': 'Proposal deleted successfully'}), 200