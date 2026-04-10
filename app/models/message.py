from datetime import datetime, timezone
from bson import ObjectId
from app import mongo


class MessageModel:
	@staticmethod
	def create_message(sender_id, recipient_id, text):
		message = {
			'sender_id': ObjectId(sender_id),
			'recipient_id': ObjectId(recipient_id),
			'text': text,
			'created_at': datetime.now(timezone.utc),
		}
		result = mongo.db.messages.insert_one(message)
		message['_id'] = result.inserted_id
		return message

	@staticmethod
	def get_between_users(user_a_id, user_b_id):
		user_a = ObjectId(user_a_id)
		user_b = ObjectId(user_b_id)

		query = {
			'$or': [
				{'sender_id': user_a, 'recipient_id': user_b},
				{'sender_id': user_b, 'recipient_id': user_a},
			]
		}

		return list(mongo.db.messages.find(query).sort('created_at', 1))

	@staticmethod
	def list_conversations_for_user(user_id):
		user_oid = ObjectId(user_id)

		pipeline = [
			{'$match': {'$or': [{'sender_id': user_oid}, {'recipient_id': user_oid}]}},
			{'$sort': {'created_at': -1}},
			{
				'$addFields': {
					'other_user_id': {
						'$cond': [
							{'$eq': ['$sender_id', user_oid]},
							'$recipient_id',
							'$sender_id'
						]
					}
				}
			},
			{
				'$group': {
					'_id': '$other_user_id',
					'lastMessage': {'$first': '$text'},
					'lastTimestamp': {'$first': '$created_at'}
				}
			},
			{'$sort': {'lastTimestamp': -1}}
		]

		return list(mongo.db.messages.aggregate(pipeline))
