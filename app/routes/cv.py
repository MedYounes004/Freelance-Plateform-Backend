from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from bson import ObjectId
from datetime import datetime, timezone

cv_bp = Blueprint('cv', __name__)

# ── Upload CV ──────────────────────────────
@cv_bp.route('/api/cv/upload', methods=['POST'])
@jwt_required()
def upload_cv():
    user_id = get_jwt_identity()
    data = request.get_json()

    file_name = data.get('name')
    file_data = data.get('data')   # base64
    file_size = data.get('size')

    if not all([file_name, file_data, file_size]):
        return jsonify({'message': 'Missing file data'}), 400

    cv = {
        'user_id': user_id,
        'name': file_name,
        'data': file_data,
        'size': file_size,
        'isPrimary': False,
        'uploadDate': datetime.now(timezone.utc).strftime('%b %d, %Y')
    }

    result = mongo.db.cvs.insert_one(cv)

    return jsonify({
        'id': str(result.inserted_id),
        'name': file_name,
        'size': file_size,
        'uploadDate': cv['uploadDate'],
        'isPrimary': False
    }), 201


# ── Get all CVs ────────────────────────────
@cv_bp.route('/api/cv', methods=['GET'])
@jwt_required()
def get_cvs():
    user_id = get_jwt_identity()
    cvs = mongo.db.cvs.find({'user_id': user_id})

    result = []
    for cv in cvs:
        result.append({
            'id': str(cv['_id']),
            'name': cv.get('name'),
            'size': cv.get('size'),
            'uploadDate': cv.get('uploadDate'),
            'isPrimary': cv.get('isPrimary', False)
        })

    return jsonify(result), 200


# ── Set Primary ────────────────────────────
@cv_bp.route('/api/cv/<cv_id>/primary', methods=['PUT'])
@jwt_required()
def set_primary(cv_id):
    user_id = get_jwt_identity()

    # Remove primary from all
    mongo.db.cvs.update_many(
        {'user_id': user_id},
        {'$set': {'isPrimary': False}}
    )

    # Set selected as primary
    mongo.db.cvs.update_one(
        {'_id': ObjectId(cv_id), 'user_id': user_id},
        {'$set': {'isPrimary': True}}
    )

    return jsonify({'message': 'Primary CV updated'}), 200


# ── Delete CV ──────────────────────────────
@cv_bp.route('/api/cv/<cv_id>', methods=['DELETE'])
@jwt_required()
def delete_cv(cv_id):
    user_id = get_jwt_identity()

    mongo.db.cvs.delete_one(
        {'_id': ObjectId(cv_id), 'user_id': user_id}
    )

    return jsonify({'message': 'CV deleted'}), 200


# ── Download CV ────────────────────────────
@cv_bp.route('/api/cv/<cv_id>/download', methods=['GET'])
@jwt_required()
def download_cv(cv_id):
    user_id = get_jwt_identity()

    cv = mongo.db.cvs.find_one(
        {'_id': ObjectId(cv_id), 'user_id': user_id}
    )

    if not cv:
        return jsonify({'message': 'CV not found'}), 404

    return jsonify({
        'name': cv.get('name'),
        'data': cv.get('data')   # base64
    }), 200