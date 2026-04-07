from app import mongo
from datetime import datetime
import uuid


class Message(mongo.Model):
    __tablename__ = 'messages'

    id = mongo.Column(mongo.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    text = mongo.Column(mongo.String(1000), nullable=False)
    sender = mongo.Column(mongo.String(255), nullable=False)
    timestamp = mongo.Column(mongo.DateTime, nullable=False, default=datetime.utcnow)
    recipient = mongo.Column(mongo.String(255), nullable=True)
    created_at = mongo.Column(mongo.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id}: {self.sender} -> {self.recipient}>'

    def to_dict(self):
        """Convert message to JSON-serializable dict"""
        return {
            'id': self.id,
            'text': self.text,
            'sender': self.sender,
            'timestamp': self.timestamp.isoformat(),
            'recipient': self.recipient,
        }
