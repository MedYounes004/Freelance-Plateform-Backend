from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import UserModel

auth_bp = Blueprint('auth', __name__)

# ── Register ──────────────────────────────
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    name     = data.get('name')
    email    = data.get('email')
    password = data.get('password')
    role     = data.get('role', 'freelancer')

    if not all([name, email, password]):
        return jsonify({'message': 'All fields are required'}), 400

    if UserModel.find_by_email(email):
        return jsonify({'message': 'Email already exists'}), 409

    user_id = UserModel.create_user(name, email, password, role)
    token = create_access_token(identity=user_id)

    return jsonify({
        'token': token,
        'user': {
            'id': user_id,
            'name': name,
            'email': email,
            'role': role,
            'subscription': 'free'
        }
    }), 201


# ── Login ──────────────────────────────────
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    email    = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password required'}), 400

    user = UserModel.find_by_email(email)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not UserModel.check_password(user['password'], password):
        return jsonify({'message': 'Invalid password'}), 401

    token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'token': token,
        'user': UserModel.serialize(user)
    }), 200


# ── Get current user ───────────────────────
@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(UserModel.serialize(user)), 200