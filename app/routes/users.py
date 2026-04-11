from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from bson import ObjectId

from app import mongo
from app.models.user import UserModel


users_bp = Blueprint('users', __name__)


def _serialize_users(users):
    return [UserModel.serialize(user) for user in users]


def _is_freelancer(user):
    role = (user.get('role') or '').strip().lower()
    return role in ('freelancer', 'work')


def _load_public_users():
    collection_names = mongo.db.list_collection_names()
    candidates = [name for name in ('users', 'user') if name in collection_names]

    if not candidates:
      candidates = collection_names

    results = []
    seen_ids = set()

    for collection_name in candidates:
        for user in mongo.db[collection_name].find({}):
            user_id = str(user.get('_id'))
            if user_id in seen_ids:
                continue

            if not user.get('name') or not user.get('email'):
                continue

            if not _is_freelancer(user):
                continue

            seen_ids.add(user_id)
            results.append(user)

    return results


@users_bp.route('/api/users/freelancers', methods=['GET'])
def public_freelancers():
    users = _load_public_users()
    return jsonify(_serialize_users(users)), 200


@users_bp.route('/api/users/available', methods=['GET', 'OPTIONS'])
def available_users():
    if request.method == 'OPTIONS':
        return '', 200

    verify_jwt_in_request()
    current_user_id = get_jwt_identity()

    role = request.args.get('role')

    query = {'_id': {'$ne': ObjectId(current_user_id)}}
    if role in ('freelancer', 'client'):
        query['role'] = role

    users = list(mongo.db.users.find(query).sort('name', 1))
    return jsonify(_serialize_users(users)), 200
