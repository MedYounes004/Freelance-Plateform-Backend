from flask import Blueprint, request, jsonify
from datetime import datetime
from bson.objectid import ObjectId
from app import mongo

messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

def get_messages_collection():
    """Get messages collection from MongoDB"""
    if mongo is None:
        raise RuntimeError('MongoDB not initialized. Call init_mongo(app) first.')
    return mongo.db.messages


def message_to_dict(doc):
    """Convert MongoDB document to dict for JSON response"""
    if doc is None:
        return None
    return {
        'id': str(doc.get('_id')),
        'text': doc.get('text'),
        'sender': doc.get('sender'),
        'recipient': doc.get('recipient'),
        'timestamp': doc.get('timestamp').isoformat() if doc.get('timestamp') else None,
        'read': doc.get('read', False),
    }


@messages_bp.route('', methods=['GET'])
def get_messages():
    """
    Fetch all messages from MongoDB.

    Optional Query Parameters:
    - sender: Filter by sender name
    - recipient: Filter by recipient name
    - limit: Number of messages to return (default 50, max 500)
    - offset: Pagination offset (default 0)

    Returns:
    List of messages sorted by timestamp (oldest first)
    """
    try:
        collection = get_messages_collection()

        sender = request.args.get('sender')
        recipient = request.args.get('recipient')
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))

        # Build filter query
        filter_query = {}
        if sender:
            filter_query['sender'] = sender
        if recipient:
            filter_query['recipient'] = recipient

        # Query with pagination
        messages = list(
            collection.find(filter_query)
            .sort('timestamp', 1)
            .skip(offset)
            .limit(limit)
        )

        return jsonify([message_to_dict(msg) for msg in messages]), 200

    except Exception as e:
        return jsonify({'error': str(e), 'type': 'GET_MESSAGES_ERROR'}), 500


@messages_bp.route('', methods=['POST'])
def send_message():
    """
    Send a new message to MongoDB.

    Request Body (JSON):
    {
        "text": "message text",
        "sender": "sender name or email",
        "recipient": "recipient name (optional)"
    }

    Returns:
    The created message with id and timestamp
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required', 'type': 'MISSING_BODY'}), 400

        text = data.get('text', '').strip()
        sender = data.get('sender', '').strip()
        recipient = data.get('recipient', '').strip() if data.get('recipient') else None

        if not text:
            return jsonify({'error': 'Message text is required', 'type': 'MISSING_TEXT'}), 400
        if not sender:
            return jsonify({'error': 'Sender is required', 'type': 'MISSING_SENDER'}), 400
        if len(text) > 1000:
            return jsonify({'error': 'Message too long (max 1000 chars)', 'type': 'TEXT_TOO_LONG'}), 400

        collection = get_messages_collection()

        # Create message document
        message_doc = {
            'text': text,
            'sender': sender,
            'recipient': recipient,
            'timestamp': datetime.utcnow(),
            'read': False,
            'created_at': datetime.utcnow(),
        }

        # Insert into MongoDB
        result = collection.insert_one(message_doc)
        message_doc['_id'] = result.inserted_id

        return jsonify(message_to_dict(message_doc)), 201

    except Exception as e:
        return jsonify({'error': str(e), 'type': 'POST_MESSAGE_ERROR'}), 500


@messages_bp.route('/<message_id>', methods=['GET'])
def get_message(message_id):
    """
    Get a single message by ID from MongoDB.
    """
    try:
        collection = get_messages_collection()

        # Convert string ID to ObjectId
        try:
            obj_id = ObjectId(message_id)
        except Exception:
            return jsonify({'error': 'Invalid message ID format', 'type': 'INVALID_ID'}), 400

        message = collection.find_one({'_id': obj_id})
        if not message:
            return jsonify({'error': 'Message not found', 'type': 'NOT_FOUND'}), 404

        return jsonify(message_to_dict(message)), 200

    except Exception as e:
        return jsonify({'error': str(e), 'type': 'GET_MESSAGE_ERROR'}), 500


@messages_bp.route('/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """
    Delete a message by ID from MongoDB.
    """
    try:
        collection = get_messages_collection()

        try:
            obj_id = ObjectId(message_id)
        except Exception:
            return jsonify({'error': 'Invalid message ID format', 'type': 'INVALID_ID'}), 400

        result = collection.delete_one({'_id': obj_id})

        if result.deleted_count == 0:
            return jsonify({'error': 'Message not found', 'type': 'NOT_FOUND'}), 404

        return jsonify({'message': 'Message deleted', 'id': message_id}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'type': 'DELETE_MESSAGE_ERROR'}), 500
