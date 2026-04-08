from app import mongo
from bson import ObjectId
from datetime import datetime


# ──────────────────────────────────────────
# Project Model
# ──────────────────────────────────────────
class ProjectModel:

    VALID_STATUSES = {'in-progress', 'completed', 'pending'}

    @staticmethod
    def _to_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    @staticmethod
    def create(data: dict, client_id: str) -> str:
        project = {
            'title':           data['title'],
            'client':          data.get('client', ''),
            'client_id':       client_id,
            'client_avatar':   data.get('clientAvatar', ''),
            'status':          data.get('status', 'pending'),
            'budget':          ProjectModel._to_float(data.get('budget', 0)),
            'deadline':        data.get('deadline', ''),
            'progress':        ProjectModel._to_int(data.get('progress', 0)),
            'category':        data.get('category', ''),
            'duration':        data.get('duration', ''),
            'proposals_count': 0,
            'description':     data.get('description', []),
            'skills':          data.get('skills', []),
            'attachments':     data.get('attachments', []),
            'milestones':      [
                {
                    'id':      str(ObjectId()),
                    'title':   m.get('title', ''),
                    'status':  m.get('status', 'pending'),
                    'payment': ProjectModel._to_float(m.get('payment', 0)),
                }
                for m in data.get('milestones', [])
            ],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        result = mongo.db.projects.insert_one(project)
        return str(result.inserted_id)

    @staticmethod
    def find_all(page=1, limit=10, status=None, category=None, skill=None) -> dict:
        query = {}
        if status:
            query['status'] = status
        if category:
            query['category'] = {'$regex': category, '$options': 'i'}
        if skill:
            query['skills'] = {'$elemMatch': {'$regex': skill, '$options': 'i'}}

        total = mongo.db.projects.count_documents(query)
        cursor = (
            mongo.db.projects.find(query)
            .sort('created_at', -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        return {
            'projects': [ProjectModel.serialize(p) for p in cursor],
            'total':    total,
            'page':     page,
            'limit':    limit,
            'pages':    (total + limit - 1) // limit if limit else 1,
        }

    @staticmethod
    def search(q: str, page=1, limit=10) -> dict:
        query = {
            '$or': [
                {'title':    {'$regex': q, '$options': 'i'}},
                {'client':   {'$regex': q, '$options': 'i'}},
                {'category': {'$regex': q, '$options': 'i'}},
                {'skills':   {'$elemMatch': {'$regex': q, '$options': 'i'}}},
            ]
        }
        total = mongo.db.projects.count_documents(query)
        cursor = (
            mongo.db.projects.find(query)
            .sort('created_at', -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        return {
            'projects': [ProjectModel.serialize(p) for p in cursor],
            'total':    total,
            'page':     page,
            'limit':    limit,
            'pages':    (total + limit - 1) // limit if limit else 1,
        }

    @staticmethod
    def find_by_id(project_id: str):
        try:
            return mongo.db.projects.find_one({'_id': ObjectId(project_id)})
        except Exception:
            return None

    @staticmethod
    def find_by_client(client_id: str) -> dict:
        cursor = mongo.db.projects.find({'client_id': client_id}).sort('created_at', -1)
        projects = [ProjectModel.serialize(p) for p in cursor]
        return {'projects': projects, 'total': len(projects)}

    @staticmethod
    def update(project_id: str, data: dict) -> bool:
        field_map = {
            'title':          'title',
            'client':         'client',
            'clientAvatar':   'client_avatar',
            'status':         'status',
            'budget':         'budget',
            'deadline':       'deadline',
            'progress':       'progress',
            'category':       'category',
            'duration':       'duration',
            'description':    'description',
            'skills':         'skills',
            'attachments':    'attachments',
        }
        updates = {'updated_at': datetime.utcnow()}
        for json_key, mongo_key in field_map.items():
            if json_key in data:
                updates[mongo_key] = data[json_key]

        result = mongo.db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': updates}
        )
        return result.matched_count > 0
#action métier spécifique, pas juste “éditer un champ "On peut appliquer
# des règles dédiées plus strictes (validation du status, permissions, transitions autorisées).
# qui a changé le status et quand
    @staticmethod
    def update_status(project_id: str, status: str) -> bool:
        result = mongo.db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
        return result.matched_count > 0

    @staticmethod
    def delete(project_id: str) -> bool:
        result = mongo.db.projects.delete_one({'_id': ObjectId(project_id)})
        # Also delete related proposals
        mongo.db.proposals.delete_many({'project_id': project_id})
        return result.deleted_count > 0

    @staticmethod
    def increment_proposals(project_id: str, delta: int = 1):
        mongo.db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$inc': {'proposals_count': delta}}
        )

    @staticmethod
    def serialize(project: dict, include_details=False) -> dict:
        if not project:
            return {}
        data = {
            'id':             str(project['_id']),
            'title':          project.get('title', ''),
            'client':         project.get('client', ''),
            'clientId':       project.get('client_id', ''),
            'clientAvatar':   project.get('client_avatar', ''),
            'status':         project.get('status', 'pending'),
            'budget':         project.get('budget', 0),
            'deadline':       project.get('deadline', ''),
            'progress':       project.get('progress', 0),
            'category':       project.get('category', ''),
            'duration':       project.get('duration', ''),
            'proposalsCount': project.get('proposals_count', 0),
            'createdAt':      project['created_at'].isoformat() if project.get('created_at') else None,
            'updatedAt':      project['updated_at'].isoformat() if project.get('updated_at') else None,
        }
        data['description'] = project.get('description', [])
        data['skills']      = project.get('skills', [])
        data['attachments'] = project.get('attachments', [])
        data['milestones']  = project.get('milestones', [])
        return data


# ──────────────────────────────────────────
# Proposal Model
# ──────────────────────────────────────────
class ProposalModel:

    VALID_STATUSES = {'pending', 'accepted', 'rejected', 'withdrawn'}

    @staticmethod
    def create(data: dict, freelancer_id: str) -> str:
        proposal = {
            'project_id':    data['projectId'],
            'freelancer_id': freelancer_id,
            'cover_letter':  data.get('coverLetter', ''),
            'bid_amount':    float(data.get('bidAmount', 0)),
            'delivery_time': data.get('deliveryTime', ''),
            'status':        'pending',
            'created_at':    datetime.utcnow(),
            'updated_at':    datetime.utcnow(),
        }
        result = mongo.db.proposals.insert_one(proposal)
        return str(result.inserted_id)

    @staticmethod
    def find_by_project(project_id: str, page=1, limit=10) -> dict:
        query = {'project_id': project_id}
        total = mongo.db.proposals.count_documents(query)
        cursor = (
            mongo.db.proposals.find(query)
            .sort('created_at', -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        return {
            'proposals': [ProposalModel.serialize(p) for p in cursor],
            'total':     total,
            'page':      page,
            'limit':     limit,
            'pages':     (total + limit - 1) // limit if limit else 1,
        }

    @staticmethod
    def find_by_id(proposal_id: str):
        try:
            return mongo.db.proposals.find_one({'_id': ObjectId(proposal_id)})
        except Exception:
            return None

    @staticmethod
    def update(proposal_id: str, data: dict) -> bool:
        updates = {'updated_at': datetime.utcnow()}
        for key in ('coverLetter', 'bidAmount', 'deliveryTime'):
            if key in data:
                mongo_key = {
                    'coverLetter':  'cover_letter',
                    'bidAmount':    'bid_amount',
                    'deliveryTime': 'delivery_time',
                }[key]
                updates[mongo_key] = data[key]

        result = mongo.db.proposals.update_one(
            {'_id': ObjectId(proposal_id)},
            {'$set': updates}
        )
        return result.matched_count > 0

    @staticmethod
    def update_status(proposal_id: str, status: str) -> bool:
        result = mongo.db.proposals.update_one(
            {'_id': ObjectId(proposal_id)},
            {'$set': {'status': status, 'updated_at': datetime.utcnow()}}
        )
        return result.matched_count > 0

    @staticmethod
    def delete(proposal_id: str):
        proposal = ProposalModel.find_by_id(proposal_id)
        if not proposal:
            return False, None
        mongo.db.proposals.delete_one({'_id': ObjectId(proposal_id)})
        return True, proposal.get('project_id')

    @staticmethod
    def serialize(proposal: dict) -> dict:
        if not proposal:
            return {}
        return {
            'id':           str(proposal['_id']),
            'projectId':    proposal.get('project_id', ''),
            'freelancerId': proposal.get('freelancer_id', ''),
            'coverLetter':  proposal.get('cover_letter', ''),
            'bidAmount':    proposal.get('bid_amount', 0),
            'deliveryTime': proposal.get('delivery_time', ''),
            'status':       proposal.get('status', 'pending'),
            'createdAt':    proposal['created_at'].isoformat() if proposal.get('created_at') else None,
            'updatedAt':    proposal['updated_at'].isoformat() if proposal.get('updated_at') else None,
        }