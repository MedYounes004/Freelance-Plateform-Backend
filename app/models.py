from app import mongo, bcrypt
from bson import ObjectId
from datetime import datetime


# ──────────────────────────────────────────
# User Model
# ──────────────────────────────────────────
class UserModel:

    @staticmethod
    def create_user(name, email, password, role='freelancer'):
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = {
            'name': name,
            'email': email,
            'password': hashed,
            'role': role,
            'subscription': 'free',
            'created_at': datetime.utcnow()
        }
        result = mongo.db.users.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({'email': email})

    @staticmethod
    def find_by_id(user_id):
        return mongo.db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def check_password(hashed, password):
        return bcrypt.check_password_hash(hashed, password)

    @staticmethod
    def serialize(user):
        return {
            'id': str(user['_id']),
            'name': user.get('name'),
            'email': user.get('email'),
            'role': user.get('role'),
            'subscription': user.get('subscription'),
        }