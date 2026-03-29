from app import mongo
from bson import ObjectId
from datetime import datetime, timezone

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
            'created_at':    datetime.now(timezone.utc),
            'updated_at':    datetime.now(timezone.utc),
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
        updates = {'updated_at': datetime.now(timezone.utc)}
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
            {'$set': {'status': status, 'updated_at': datetime.now(timezone.utc)}}
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