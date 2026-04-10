from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from bson import ObjectId

from app import mongo
from app.models.user import UserModel


users_bp = Blueprint('users', __name__)


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
    return jsonify([UserModel.serialize(user) for user in users]), 200
