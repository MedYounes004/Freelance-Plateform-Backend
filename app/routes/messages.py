from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

from app.models.user import UserModel
from app.models.message import MessageModel


messages_bp = Blueprint('messages', __name__)


def _serialize_message(message):
	return {
		'id': str(message['_id']),
		'senderId': str(message['sender_id']),
		'recipientId': str(message['recipient_id']),
		'text': message.get('text', ''),
		'timestamp': message.get('created_at').isoformat() if message.get('created_at') else None,
	}


@messages_bp.route('/api/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
	user_id = get_jwt_identity()

	try:
		rows = MessageModel.list_conversations_for_user(user_id)
	except Exception:
		return jsonify({'message': 'Invalid user id'}), 400

	result = []
	for row in rows:
		other_id = str(row['_id'])
		other_user = UserModel.find_by_id(other_id)
		if not other_user:
			continue

		result.append({
			'userId': other_id,
			'name': other_user.get('name') or other_user.get('email'),
			'lastMessage': row.get('lastMessage', ''),
			'timestamp': row.get('lastTimestamp').isoformat() if row.get('lastTimestamp') else None,
		})

	return jsonify(result), 200


@messages_bp.route('/api/messages/<recipient_id>', methods=['GET'])
@jwt_required()
def get_messages(recipient_id):
	sender_id = get_jwt_identity()

	try:
		ObjectId(recipient_id)
	except Exception:
		return jsonify({'message': 'Invalid recipient id'}), 400

	messages = MessageModel.get_between_users(sender_id, recipient_id)
	return jsonify([_serialize_message(msg) for msg in messages]), 200


@messages_bp.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
	sender_id = get_jwt_identity()
	data = request.get_json() or {}

	text = (data.get('text') or '').strip()
	recipient_id = (data.get('recipientId') or '').strip()

	if not text or not recipient_id:
		return jsonify({'message': 'text and recipientId are required'}), 400

	if recipient_id == sender_id:
		return jsonify({'message': 'Cannot send message to yourself'}), 400

	try:
		recipient = UserModel.find_by_id(recipient_id)
	except Exception:
		recipient = None

	if not recipient:
		return jsonify({'message': 'Recipient not found'}), 404

	message = MessageModel.create_message(sender_id, recipient_id, text)
	return jsonify(_serialize_message(message)), 201
