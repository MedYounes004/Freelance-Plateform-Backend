from app import mongo
from bson import ObjectId
from datetime import datetime, timezone

# ──────────────────────────────────────────
# Project Model
# ──────────────────────────────────────────
class ProjectModel:

    VALID_STATUSES = {'in-progress', 'completed', 'pending'}

    @staticmethod
    def create(data: dict, client_id: str) -> str:
        project = {
            'title':           data['title'],
            'client':          data['client'],
            'client_id':       client_id,
            'client_avatar':   data.get('clientAvatar', ''),
            'status':          data.get('status', 'pending'),
            'budget':          float(data.get('budget', 0)),
            'deadline':        data.get('deadline', ''),
            'progress':        int(data.get('progress', 0)),
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
                    'payment': float(m.get('payment', 0)),
                }
                for m in data.get('milestones', [])
            ],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
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
        updates = {'updated_at': datetime.now(timezone.utc)}
        for json_key, mongo_key in field_map.items():
            if json_key in data:
                updates[mongo_key] = data[json_key]

        result = mongo.db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': updates}
        )
        return result.matched_count > 0

    @staticmethod
    def update_status(project_id: str, status: str) -> bool:
        result = mongo.db.projects.update_one(
            {'_id': ObjectId(project_id)},
            {'$set': {'status': status, 'updated_at': datetime.now(timezone.utc)}}
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
    def serialize(project: dict) -> dict:
        if not project:
            return {}
        data = {'id': str(project['_id']), 'title': project.get('title', ''), 'client': project.get('client', ''),
                'clientId': project.get('client_id', ''), 'clientAvatar': project.get('client_avatar', ''),
                'status': project.get('status', 'pending'), 'budget': project.get('budget', 0),
                'deadline': project.get('deadline', ''), 'progress': project.get('progress', 0),
                'category': project.get('category', ''), 'duration': project.get('duration', ''),
                'proposalsCount': project.get('proposals_count', 0),
                'createdAt': project['created_at'].isoformat() if project.get('created_at') else None,
                'updatedAt': project['updated_at'].isoformat() if project.get('updated_at') else None,
                'description': project.get('description', []), 'skills': project.get('skills', []),
                'attachments': project.get('attachments', []), 'milestones': project.get('milestones', [])}
        # Always include details (description, skills, etc.) — frontend detail page needs them
        return data
