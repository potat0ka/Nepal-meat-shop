#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced Chat Model
MongoDB models for enhanced chat system with admin takeover functionality.
"""

from datetime import datetime
from bson.objectid import ObjectId
from enum import Enum
from typing import Optional, Dict, Any, List

class MessageType(Enum):
    """Message types for chat system."""
    USER = "user"
    AI = "ai"
    ADMIN = "admin"
    SYSTEM = "system"

class ConversationStatus(Enum):
    """Conversation status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ADMIN_TAKEN = "admin_taken"
    CLOSED = "closed"

class AdminSessionStatus(Enum):
    """Admin session status types."""
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"

class ChatConversation:
    """
    MongoDB model for chat conversations.
    Each conversation represents a chat session with a customer.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.session_id = data.get('session_id')  # Unique session identifier
            self.customer_id = data.get('customer_id')  # User ID if logged in, None for anonymous
            self.customer_ip = data.get('customer_ip')  # IP address for anonymous users
            self.customer_user_agent = data.get('customer_user_agent')  # Browser info
            self.status = data.get('status', ConversationStatus.ACTIVE.value)
            self.created_at = data.get('created_at', datetime.utcnow())
            self.updated_at = data.get('updated_at', datetime.utcnow())
            self.last_activity = data.get('last_activity', datetime.utcnow())
            
            # Admin takeover fields
            self.admin_taken_by = data.get('admin_taken_by')  # Admin user ID who took over
            self.admin_taken_at = data.get('admin_taken_at')  # When admin took over
            self.is_admin_active = data.get('is_admin_active', False)  # Is admin currently handling
            
            # Metadata
            self.language_detected = data.get('language_detected', 'en')
            self.total_messages = data.get('total_messages', 0)
            self.customer_satisfaction = data.get('customer_satisfaction')  # 1-5 rating
            self.tags = data.get('tags', [])  # For categorization
            
        else:
            self._id = None
            self.session_id = None
            self.customer_id = None
            self.customer_ip = None
            self.customer_user_agent = None
            self.status = ConversationStatus.ACTIVE.value
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.last_activity = datetime.utcnow()
            self.admin_taken_by = None
            self.admin_taken_at = None
            self.is_admin_active = False
            self.language_detected = 'en'
            self.total_messages = 0
            self.customer_satisfaction = None
            self.tags = []
    
    @property
    def id(self):
        """Return string representation of ObjectId."""
        return str(self._id) if self._id else None
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        data = {
            'session_id': self.session_id,
            'customer_id': self.customer_id,
            'customer_ip': self.customer_ip,
            'customer_user_agent': self.customer_user_agent,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_activity': self.last_activity,
            'admin_taken_by': self.admin_taken_by,
            'admin_taken_at': self.admin_taken_at,
            'is_admin_active': self.is_admin_active,
            'language_detected': self.language_detected,
            'total_messages': self.total_messages,
            'customer_satisfaction': self.customer_satisfaction,
            'tags': self.tags
        }
        
        # Only include _id if it exists (not None)
        if self._id is not None:
            data['_id'] = self._id
            
        return data
    
    def to_json_dict(self):
        """Convert to JSON-serializable dictionary."""
        data = self.to_dict()
        
        # Convert ObjectId to string
        if data.get('_id'):
            data['_id'] = str(data['_id'])
        if data.get('customer_id'):
            data['customer_id'] = str(data['customer_id'])
        if data.get('admin_taken_by'):
            data['admin_taken_by'] = str(data['admin_taken_by'])
        
        # Convert datetime to ISO format
        for field in ['created_at', 'updated_at', 'last_activity', 'admin_taken_at']:
            if data.get(field):
                data[field] = data[field].isoformat()
        
        return data

class ChatMessage:
    """
    MongoDB model for individual chat messages.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.conversation_id = data.get('conversation_id')  # Reference to ChatConversation
            self.session_id = data.get('session_id')  # For quick lookup
            self.message_type = data.get('message_type', MessageType.USER.value)
            self.content = data.get('content')
            self.timestamp = data.get('timestamp', datetime.utcnow())
            
            # Sender information
            self.sender_id = data.get('sender_id')  # User ID or Admin ID
            self.sender_name = data.get('sender_name')  # Display name
            self.sender_ip = data.get('sender_ip')  # IP address
            
            # AI-specific fields
            self.ai_response_source = data.get('ai_response_source')  # 'ai', 'cache', 'fallback'
            self.ai_confidence = data.get('ai_confidence', 0.0)
            self.ai_response_time_ms = data.get('ai_response_time_ms')
            
            # Admin-specific fields
            self.is_admin_message = data.get('is_admin_message', False)
            self.admin_id = data.get('admin_id')  # Admin who sent the message
            self.appears_as_ai = data.get('appears_as_ai', False)  # Admin message appearing as AI
            
            # Metadata
            self.language_detected = data.get('language_detected')
            self.read_by_customer = data.get('read_by_customer', False)
            self.read_by_admin = data.get('read_by_admin', False)
            self.edited = data.get('edited', False)
            self.edited_at = data.get('edited_at')
            
        else:
            self._id = None
            self.conversation_id = None
            self.session_id = None
            self.message_type = MessageType.USER.value
            self.content = None
            self.timestamp = datetime.utcnow()
            self.sender_id = None
            self.sender_name = None
            self.sender_ip = None
            self.ai_response_source = None
            self.ai_confidence = 0.0
            self.ai_response_time_ms = None
            self.is_admin_message = False
            self.admin_id = None
            self.appears_as_ai = False
            self.language_detected = None
            self.read_by_customer = False
            self.read_by_admin = False
            self.edited = False
            self.edited_at = None
    
    @property
    def id(self):
        """Return string representation of ObjectId."""
        return str(self._id) if self._id else None
    
    def to_dict(self):
        """Convert message to dictionary."""
        data = {
            'conversation_id': self.conversation_id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'sender_ip': self.sender_ip,
            'ai_response_source': self.ai_response_source,
            'ai_confidence': self.ai_confidence,
            'ai_response_time_ms': self.ai_response_time_ms,
            'is_admin_message': self.is_admin_message,
            'admin_id': self.admin_id,
            'appears_as_ai': self.appears_as_ai,
            'language_detected': self.language_detected,
            'read_by_customer': self.read_by_customer,
            'read_by_admin': self.read_by_admin,
            'edited': self.edited,
            'edited_at': self.edited_at
        }
        
        # Only include _id if it exists (not None)
        if self._id is not None:
            data['_id'] = self._id
            
        return data
    
    def to_json_dict(self):
        """Convert to JSON-serializable dictionary."""
        data = self.to_dict()
        
        # Convert ObjectId to string
        for field in ['_id', 'conversation_id', 'sender_id', 'admin_id']:
            if data.get(field):
                data[field] = str(data[field])
        
        # Convert datetime to ISO format
        for field in ['timestamp', 'edited_at']:
            if data.get(field):
                data[field] = data[field].isoformat()
        
        return data

class AdminSession:
    """
    MongoDB model for admin chat sessions.
    Tracks which admins are online and available for chat takeover.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.admin_id = data.get('admin_id')  # Reference to admin user
            self.admin_name = data.get('admin_name')  # Display name
            self.status = data.get('status', AdminSessionStatus.ONLINE.value)
            self.socket_id = data.get('socket_id')  # WebSocket connection ID
            self.last_seen = data.get('last_seen', datetime.utcnow())
            self.login_time = data.get('login_time', datetime.utcnow())
            self.active_conversations = data.get('active_conversations', [])  # List of conversation IDs
            self.max_conversations = data.get('max_conversations', 5)  # Max concurrent chats
            
        else:
            self._id = None
            self.admin_id = None
            self.admin_name = None
            self.status = AdminSessionStatus.ONLINE.value
            self.socket_id = None
            self.last_seen = datetime.utcnow()
            self.login_time = datetime.utcnow()
            self.active_conversations = []
            self.max_conversations = 5
    
    @property
    def id(self):
        """Return string representation of ObjectId."""
        return str(self._id) if self._id else None
    
    def to_dict(self):
        """Convert admin session to dictionary."""
        return {
            '_id': self._id,
            'admin_id': self.admin_id,
            'admin_name': self.admin_name,
            'status': self.status,
            'socket_id': self.socket_id,
            'last_seen': self.last_seen,
            'login_time': self.login_time,
            'active_conversations': self.active_conversations,
            'max_conversations': self.max_conversations
        }
    
    def to_json_dict(self):
        """Convert to JSON-serializable dictionary."""
        data = self.to_dict()
        
        # Convert ObjectId to string
        if data.get('_id'):
            data['_id'] = str(data['_id'])
        if data.get('admin_id'):
            data['admin_id'] = str(data['admin_id'])
        
        # Convert datetime to ISO format
        for field in ['last_seen', 'login_time']:
            if data.get(field):
                data[field] = data[field].isoformat()
        
        return data

# MongoDB Collection Schemas
CHAT_SCHEMAS = {
    'chat_conversations': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['session_id', 'status', 'created_at'],
                'properties': {
                    'session_id': {'bsonType': 'string'},
                    'customer_id': {'bsonType': ['objectId', 'null']},
                    'customer_ip': {'bsonType': ['string', 'null']},
                    'customer_user_agent': {'bsonType': ['string', 'null']},
                    'status': {'enum': ['active', 'inactive', 'admin_taken', 'closed']},
                    'created_at': {'bsonType': 'date'},
                    'updated_at': {'bsonType': 'date'},
                    'last_activity': {'bsonType': 'date'},
                    'admin_taken_by': {'bsonType': ['objectId', 'null']},
                    'admin_taken_at': {'bsonType': ['date', 'null']},
                    'is_admin_active': {'bsonType': 'bool'},
                    'language_detected': {'bsonType': 'string'},
                    'total_messages': {'bsonType': 'int'},
                    'customer_satisfaction': {'bsonType': ['int', 'null']},
                    'tags': {'bsonType': 'array'}
                }
            }
        },
        'indexes': [
            {'key': {'session_id': 1}, 'unique': True},
            {'key': {'customer_id': 1}},
            {'key': {'status': 1}},
            {'key': {'admin_taken_by': 1}},
            {'key': {'last_activity': 1}},
            {'key': {'created_at': 1}}
        ]
    },
    
    'chat_messages': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['conversation_id', 'session_id', 'message_type', 'content', 'timestamp'],
                'properties': {
                    'conversation_id': {'bsonType': 'objectId'},
                    'session_id': {'bsonType': 'string'},
                    'message_type': {'enum': ['user', 'ai', 'admin', 'system']},
                    'content': {'bsonType': 'string'},
                    'timestamp': {'bsonType': 'date'},
                    'sender_id': {'bsonType': ['objectId', 'null']},
                    'sender_name': {'bsonType': ['string', 'null']},
                    'sender_ip': {'bsonType': ['string', 'null']},
                    'ai_response_source': {'bsonType': ['string', 'null']},
                    'ai_confidence': {'bsonType': 'double'},
                    'ai_response_time_ms': {'bsonType': ['int', 'null']},
                    'is_admin_message': {'bsonType': 'bool'},
                    'admin_id': {'bsonType': ['objectId', 'null']},
                    'appears_as_ai': {'bsonType': 'bool'},
                    'language_detected': {'bsonType': ['string', 'null']},
                    'read_by_customer': {'bsonType': 'bool'},
                    'read_by_admin': {'bsonType': 'bool'},
                    'edited': {'bsonType': 'bool'},
                    'edited_at': {'bsonType': ['date', 'null']}
                }
            }
        },
        'indexes': [
            {'key': {'conversation_id': 1, 'timestamp': 1}},
            {'key': {'session_id': 1, 'timestamp': 1}},
            {'key': {'message_type': 1}},
            {'key': {'admin_id': 1}},
            {'key': {'timestamp': 1}}
        ]
    },
    
    'admin_sessions': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['admin_id', 'status', 'last_seen'],
                'properties': {
                    'admin_id': {'bsonType': 'objectId'},
                    'admin_name': {'bsonType': ['string', 'null']},
                    'status': {'enum': ['online', 'away', 'offline']},
                    'socket_id': {'bsonType': ['string', 'null']},
                    'last_seen': {'bsonType': 'date'},
                    'login_time': {'bsonType': 'date'},
                    'active_conversations': {'bsonType': 'array'},
                    'max_conversations': {'bsonType': 'int'}
                }
            }
        },
        'indexes': [
            {'key': {'admin_id': 1}, 'unique': True},
            {'key': {'status': 1}},
            {'key': {'socket_id': 1}},
            {'key': {'last_seen': 1}}
        ]
    }
}