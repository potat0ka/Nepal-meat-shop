#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Chat Model
MongoDB model for AI chat assistant conversations.
"""

from datetime import datetime
from bson.objectid import ObjectId

class MongoChat:
    """
    MongoDB Chat model for storing AI assistant conversations.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.user_message = data.get('user_message')
            self.bot_reply = data.get('bot_reply')
            self.timestamp = data.get('timestamp') or datetime.utcnow()
            self.user_id = data.get('user_id')  # Optional: link to user if logged in
            self.session_id = data.get('session_id')  # Optional: group related conversations
            self.language_detected = data.get('language_detected')  # Track language used
            self.response_time_ms = data.get('response_time_ms')  # Track performance
            
            # Enhanced fields for reliability and learning
            self.response_source = data.get('response_source', 'ai')  # 'ai', 'cache', 'fallback'
            self.confidence_score = data.get('confidence_score', 0.0)  # AI confidence level
            self.cached_response = data.get('cached_response', False)  # Whether response was cached
            self.user_rating = data.get('user_rating')  # User feedback rating (1-5)
            self.user_feedback = data.get('user_feedback')  # User feedback text
            self.feedback_timestamp = data.get('feedback_timestamp')  # When feedback was given
            
        else:
            self._id = None
            self.user_message = None
            self.bot_reply = None
            self.timestamp = datetime.utcnow()
            self.user_id = None
            self.session_id = None
            self.language_detected = None
            self.response_time_ms = None
            self.response_source = 'ai'
            self.confidence_score = 0.0
            self.cached_response = False
            self.user_rating = None
            self.user_feedback = None
            self.feedback_timestamp = None
    
    @property
    def id(self):
        """Return string representation of ObjectId."""
        return str(self._id) if self._id else None
    
    @property
    def created_at(self):
        """Alias for timestamp for consistency with other models."""
        return self.timestamp
    
    def to_dict(self):
        """Convert chat document to dictionary."""
        data = {
            'user_message': self.user_message,
            'bot_reply': self.bot_reply,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'language_detected': self.language_detected,
            'response_time_ms': self.response_time_ms
        }
        
        if self._id:
            data['_id'] = self._id
            
        return data
    
    def to_json_dict(self):
        """Convert to JSON-serializable dictionary."""
        data = self.to_dict()
        
        # Convert ObjectId to string for JSON serialization
        if data.get('_id'):
            data['_id'] = str(data['_id'])
        
        # Convert datetime to ISO format
        if data.get('timestamp'):
            data['timestamp'] = data['timestamp'].isoformat()
            
        return data
    
    @staticmethod
    def get_schema():
        """Return MongoDB collection schema for chat documents."""
        return {
            'user_message': {'type': 'string', 'required': True},
            'bot_reply': {'type': 'string', 'required': True},
            'timestamp': {'type': 'datetime', 'required': True, 'default': datetime.utcnow},
            'user_id': {'type': 'objectid', 'required': False},
            'session_id': {'type': 'string', 'required': False},
            'language_detected': {'type': 'string', 'required': False},
            'response_time_ms': {'type': 'number', 'required': False}
        }