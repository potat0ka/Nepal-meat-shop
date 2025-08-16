#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced Chat Model V2
MongoDB models for enhanced chat system with role-based access, internal messaging, and AI learning.
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
    INTERNAL = "internal"  # New: Internal admin-only messages
    AI_LEARNING = "ai_learning"  # New: AI learning data

class MessageVisibility(Enum):
    """Message visibility levels for role-based access."""
    PUBLIC = "public"  # Visible to customers and all admins
    ADMIN_ONLY = "admin_only"  # Visible only to admins and super admins
    INTERNAL = "internal"  # Hidden from customers, visible to admins
    SUPER_ADMIN_ONLY = "super_admin_only"  # Only super admins can see

class ConversationStatus(Enum):
    """Conversation status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ADMIN_TAKEN = "admin_taken"
    CLOSED = "closed"
    ESCALATED = "escalated"  # New: Escalated to higher level

class AdminSessionStatus(Enum):
    """Admin session status types."""
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"

class UserRole(Enum):
    """User roles for access control."""
    CUSTOMER = "customer"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ChatConversationV2:
    """
    Enhanced MongoDB model for chat conversations with role-based access.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.conversation_id = data.get('conversation_id')  # Unique conversation identifier
            self.session_id = data.get('session_id')  # Session identifier for anonymous users
            self.customer_id = data.get('customer_id')  # User ID if logged in
            self.customer_ip = data.get('customer_ip')
            self.customer_user_agent = data.get('customer_user_agent')
            self.status = data.get('status', ConversationStatus.ACTIVE.value)
            self.created_at = data.get('created_at', datetime.utcnow())
            self.updated_at = data.get('updated_at', datetime.utcnow())
            self.last_activity = data.get('last_activity', datetime.utcnow())
            
            # Admin takeover fields
            self.admin_taken_by = data.get('admin_taken_by')
            self.admin_taken_at = data.get('admin_taken_at')
            self.is_admin_active = data.get('is_admin_active', False)
            self.admin_notes = data.get('admin_notes', [])  # Internal admin notes
            
            # Enhanced metadata
            self.language_detected = data.get('language_detected', 'en')
            self.total_messages = data.get('total_messages', 0)
            self.total_internal_messages = data.get('total_internal_messages', 0)  # New
            self.customer_satisfaction = data.get('customer_satisfaction')
            self.priority_level = data.get('priority_level', 'normal')  # low, normal, high, urgent
            self.tags = data.get('tags', [])
            self.escalation_level = data.get('escalation_level', 0)  # 0=normal, 1=escalated, 2=high priority
            
            # AI Learning fields
            self.ai_learning_enabled = data.get('ai_learning_enabled', True)
            self.admin_corrections_count = data.get('admin_corrections_count', 0)
            self.ai_accuracy_score = data.get('ai_accuracy_score', 0.0)
            
        else:
            self._id = None
            self.conversation_id = None
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
            self.admin_notes = []
            self.language_detected = 'en'
            self.total_messages = 0
            self.total_internal_messages = 0
            self.customer_satisfaction = None
            self.priority_level = 'normal'
            self.tags = []
            self.escalation_level = 0
            self.ai_learning_enabled = True
            self.admin_corrections_count = 0
            self.ai_accuracy_score = 0.0
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        data = {
            'conversation_id': self.conversation_id,
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
            'admin_notes': self.admin_notes,
            'language_detected': self.language_detected,
            'total_messages': self.total_messages,
            'total_internal_messages': self.total_internal_messages,
            'customer_satisfaction': self.customer_satisfaction,
            'priority_level': self.priority_level,
            'tags': self.tags,
            'escalation_level': self.escalation_level,
            'ai_learning_enabled': self.ai_learning_enabled,
            'admin_corrections_count': self.admin_corrections_count,
            'ai_accuracy_score': self.ai_accuracy_score
        }
        
        if self._id is not None:
            data['_id'] = self._id
            
        return data

class ChatMessageV2:
    """
    Enhanced MongoDB model for individual chat messages with role-based visibility.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.conversation_id = data.get('conversation_id')
            self.session_id = data.get('session_id')
            self.message_type = data.get('message_type', MessageType.USER.value)
            self.content = data.get('content')
            self.timestamp = data.get('timestamp', datetime.utcnow())
            
            # Enhanced visibility and access control
            self.visibility = data.get('visibility', MessageVisibility.PUBLIC.value)
            self.is_internal = data.get('is_internal', False)  # Quick flag for internal messages
            self.visible_to_roles = data.get('visible_to_roles', ['customer', 'admin', 'super_admin'])
            
            # Sender information
            self.sender_id = data.get('sender_id')
            self.sender_name = data.get('sender_name')
            self.sender_role = data.get('sender_role', UserRole.CUSTOMER.value)
            self.sender_ip = data.get('sender_ip')
            
            # AI-specific fields
            self.ai_response_source = data.get('ai_response_source')
            self.ai_confidence = data.get('ai_confidence', 0.0)
            self.ai_response_time_ms = data.get('ai_response_time_ms')
            self.ai_model_used = data.get('ai_model_used')  # Track which AI model was used
            
            # Admin-specific fields
            self.is_admin_message = data.get('is_admin_message', False)
            self.admin_id = data.get('admin_id')
            self.appears_as_ai = data.get('appears_as_ai', False)  # Admin message appearing as AI
            self.admin_override = data.get('admin_override', False)  # Admin correcting AI
            
            # Message metadata
            self.language_detected = data.get('language_detected')
            self.read_by_customer = data.get('read_by_customer', False)
            self.read_by_admin = data.get('read_by_admin', False)
            self.edited = data.get('edited', False)
            self.edited_at = data.get('edited_at')
            self.edited_by = data.get('edited_by')
            
            # Internal messaging fields
            self.internal_note = data.get('internal_note')  # Internal admin note
            self.internal_tags = data.get('internal_tags', [])  # Tags for internal categorization
            self.escalation_flag = data.get('escalation_flag', False)  # Flag for escalation
            
            # AI Learning fields
            self.is_training_data = data.get('is_training_data', False)
            self.admin_correction = data.get('admin_correction')  # Admin's correction to AI response
            self.correction_reason = data.get('correction_reason')  # Why admin corrected
            self.learning_feedback = data.get('learning_feedback')  # Feedback for AI improvement
            
        else:
            self._id = None
            self.conversation_id = None
            self.session_id = None
            self.message_type = MessageType.USER.value
            self.content = None
            self.timestamp = datetime.utcnow()
            self.visibility = MessageVisibility.PUBLIC.value
            self.is_internal = False
            self.visible_to_roles = ['customer', 'admin', 'super_admin']
            self.sender_id = None
            self.sender_name = None
            self.sender_role = UserRole.CUSTOMER.value
            self.sender_ip = None
            self.ai_response_source = None
            self.ai_confidence = 0.0
            self.ai_response_time_ms = None
            self.ai_model_used = None
            self.is_admin_message = False
            self.admin_id = None
            self.appears_as_ai = False
            self.admin_override = False
            self.language_detected = None
            self.read_by_customer = False
            self.read_by_admin = False
            self.edited = False
            self.edited_at = None
            self.edited_by = None
            self.internal_note = None
            self.internal_tags = []
            self.escalation_flag = False
            self.is_training_data = False
            self.admin_correction = None
            self.correction_reason = None
            self.learning_feedback = None
    
    def is_visible_to_role(self, user_role: str) -> bool:
        """
        Check if message is visible to a specific user role.
        """
        if self.is_internal and user_role == UserRole.CUSTOMER.value:
            return False
        
        if self.visibility == MessageVisibility.SUPER_ADMIN_ONLY.value:
            return user_role == UserRole.SUPER_ADMIN.value
        
        if self.visibility == MessageVisibility.ADMIN_ONLY.value:
            return user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        
        if self.visibility == MessageVisibility.INTERNAL.value:
            return user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        
        return user_role in self.visible_to_roles
    
    def to_dict(self):
        """Convert message to dictionary."""
        data = {
            'conversation_id': self.conversation_id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp,
            'visibility': self.visibility,
            'is_internal': self.is_internal,
            'visible_to_roles': self.visible_to_roles,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'sender_role': self.sender_role,
            'sender_ip': self.sender_ip,
            'ai_response_source': self.ai_response_source,
            'ai_confidence': self.ai_confidence,
            'ai_response_time_ms': self.ai_response_time_ms,
            'ai_model_used': self.ai_model_used,
            'is_admin_message': self.is_admin_message,
            'admin_id': self.admin_id,
            'appears_as_ai': self.appears_as_ai,
            'admin_override': self.admin_override,
            'language_detected': self.language_detected,
            'read_by_customer': self.read_by_customer,
            'read_by_admin': self.read_by_admin,
            'edited': self.edited,
            'edited_at': self.edited_at,
            'edited_by': self.edited_by,
            'internal_note': self.internal_note,
            'internal_tags': self.internal_tags,
            'escalation_flag': self.escalation_flag,
            'is_training_data': self.is_training_data,
            'admin_correction': self.admin_correction,
            'correction_reason': self.correction_reason,
            'learning_feedback': self.learning_feedback
        }
        
        if self._id is not None:
            data['_id'] = self._id
            
        return data

class AILearningData:
    """
    Model for storing AI learning data from admin corrections.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.conversation_id = data.get('conversation_id')
            self.original_message = data.get('original_message')  # Customer's original message
            self.ai_response = data.get('ai_response')  # AI's original response
            self.admin_correction = data.get('admin_correction')  # Admin's corrected response
            self.correction_reason = data.get('correction_reason')  # Why it was corrected
            self.improvement_category = data.get('improvement_category')  # Category of improvement
            self.language = data.get('language', 'en')
            self.created_at = data.get('created_at', datetime.utcnow())
            self.admin_id = data.get('admin_id')
            self.admin_name = data.get('admin_name')
            self.confidence_before = data.get('confidence_before', 0.0)
            self.confidence_after = data.get('confidence_after', 0.0)
            self.applied_to_training = data.get('applied_to_training', False)
            self.training_applied_at = data.get('training_applied_at')
        else:
            self._id = None
            self.conversation_id = None
            self.original_message = None
            self.ai_response = None
            self.admin_correction = None
            self.correction_reason = None
            self.improvement_category = None
            self.language = 'en'
            self.created_at = datetime.utcnow()
            self.admin_id = None
            self.admin_name = None
            self.confidence_before = 0.0
            self.confidence_after = 0.0
            self.applied_to_training = False
            self.training_applied_at = None
    
    def to_dict(self):
        """Convert to dictionary."""
        data = {
            'conversation_id': self.conversation_id,
            'original_message': self.original_message,
            'ai_response': self.ai_response,
            'admin_correction': self.admin_correction,
            'correction_reason': self.correction_reason,
            'improvement_category': self.improvement_category,
            'language': self.language,
            'created_at': self.created_at,
            'admin_id': self.admin_id,
            'admin_name': self.admin_name,
            'confidence_before': self.confidence_before,
            'confidence_after': self.confidence_after,
            'applied_to_training': self.applied_to_training,
            'training_applied_at': self.training_applied_at
        }
        
        if self._id is not None:
            data['_id'] = self._id
            
        return data

# Enhanced MongoDB Collection Schemas
ENHANCED_CHAT_SCHEMAS = {
    'chat_conversations_v2': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['conversation_id', 'status', 'created_at'],
                'properties': {
                    'conversation_id': {'bsonType': 'string'},
                    'session_id': {'bsonType': ['string', 'null']},
                    'customer_id': {'bsonType': ['objectId', 'null']},
                    'customer_ip': {'bsonType': ['string', 'null']},
                    'customer_user_agent': {'bsonType': ['string', 'null']},
                    'status': {'enum': ['active', 'inactive', 'admin_taken', 'closed', 'escalated']},
                    'created_at': {'bsonType': 'date'},
                    'updated_at': {'bsonType': 'date'},
                    'last_activity': {'bsonType': 'date'},
                    'admin_taken_by': {'bsonType': ['objectId', 'null']},
                    'admin_taken_at': {'bsonType': ['date', 'null']},
                    'is_admin_active': {'bsonType': 'bool'},
                    'admin_notes': {'bsonType': 'array'},
                    'language_detected': {'bsonType': 'string'},
                    'total_messages': {'bsonType': 'int'},
                    'total_internal_messages': {'bsonType': 'int'},
                    'customer_satisfaction': {'bsonType': ['int', 'null']},
                    'priority_level': {'enum': ['low', 'normal', 'high', 'urgent']},
                    'tags': {'bsonType': 'array'},
                    'escalation_level': {'bsonType': 'int'},
                    'ai_learning_enabled': {'bsonType': 'bool'},
                    'admin_corrections_count': {'bsonType': 'int'},
                    'ai_accuracy_score': {'bsonType': 'double'}
                }
            }
        },
        'indexes': [
            {'key': {'conversation_id': 1}, 'unique': True},
            {'key': {'session_id': 1}},
            {'key': {'customer_id': 1}},
            {'key': {'status': 1}},
            {'key': {'admin_taken_by': 1}},
            {'key': {'last_activity': 1}},
            {'key': {'priority_level': 1}},
            {'key': {'escalation_level': 1}},
            {'key': {'created_at': 1}}
        ]
    },
    
    'chat_messages_v2': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['conversation_id', 'message_type', 'content', 'timestamp', 'visibility'],
                'properties': {
                    'conversation_id': {'bsonType': 'objectId'},
                    'session_id': {'bsonType': ['string', 'null']},
                    'message_type': {'enum': ['user', 'ai', 'admin', 'system', 'internal', 'ai_learning']},
                    'content': {'bsonType': 'string'},
                    'timestamp': {'bsonType': 'date'},
                    'visibility': {'enum': ['public', 'admin_only', 'internal', 'super_admin_only']},
                    'is_internal': {'bsonType': 'bool'},
                    'visible_to_roles': {'bsonType': 'array'},
                    'sender_id': {'bsonType': ['objectId', 'null']},
                    'sender_name': {'bsonType': ['string', 'null']},
                    'sender_role': {'enum': ['customer', 'user', 'admin', 'super_admin']},
                    'sender_ip': {'bsonType': ['string', 'null']},
                    'ai_response_source': {'bsonType': ['string', 'null']},
                    'ai_confidence': {'bsonType': 'double'},
                    'ai_response_time_ms': {'bsonType': ['int', 'null']},
                    'ai_model_used': {'bsonType': ['string', 'null']},
                    'is_admin_message': {'bsonType': 'bool'},
                    'admin_id': {'bsonType': ['objectId', 'null']},
                    'appears_as_ai': {'bsonType': 'bool'},
                    'admin_override': {'bsonType': 'bool'},
                    'language_detected': {'bsonType': ['string', 'null']},
                    'read_by_customer': {'bsonType': 'bool'},
                    'read_by_admin': {'bsonType': 'bool'},
                    'edited': {'bsonType': 'bool'},
                    'edited_at': {'bsonType': ['date', 'null']},
                    'edited_by': {'bsonType': ['objectId', 'null']},
                    'internal_note': {'bsonType': ['string', 'null']},
                    'internal_tags': {'bsonType': 'array'},
                    'escalation_flag': {'bsonType': 'bool'},
                    'is_training_data': {'bsonType': 'bool'},
                    'admin_correction': {'bsonType': ['string', 'null']},
                    'correction_reason': {'bsonType': ['string', 'null']},
                    'learning_feedback': {'bsonType': ['string', 'null']}
                }
            }
        },
        'indexes': [
            {'key': {'conversation_id': 1, 'timestamp': 1}},
            {'key': {'session_id': 1, 'timestamp': 1}},
            {'key': {'message_type': 1}},
            {'key': {'visibility': 1}},
            {'key': {'is_internal': 1}},
            {'key': {'admin_id': 1}},
            {'key': {'sender_role': 1}},
            {'key': {'escalation_flag': 1}},
            {'key': {'is_training_data': 1}},
            {'key': {'timestamp': 1}}
        ]
    },
    
    'ai_learning_data': {
        'validator': {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['conversation_id', 'original_message', 'ai_response', 'admin_correction', 'created_at'],
                'properties': {
                    'conversation_id': {'bsonType': 'objectId'},
                    'original_message': {'bsonType': 'string'},
                    'ai_response': {'bsonType': 'string'},
                    'admin_correction': {'bsonType': 'string'},
                    'correction_reason': {'bsonType': ['string', 'null']},
                    'improvement_category': {'bsonType': ['string', 'null']},
                    'language': {'bsonType': 'string'},
                    'created_at': {'bsonType': 'date'},
                    'admin_id': {'bsonType': ['objectId', 'null']},
                    'admin_name': {'bsonType': ['string', 'null']},
                    'confidence_before': {'bsonType': 'double'},
                    'confidence_after': {'bsonType': 'double'},
                    'applied_to_training': {'bsonType': 'bool'},
                    'training_applied_at': {'bsonType': ['date', 'null']}
                }
            }
        },
        'indexes': [
            {'key': {'conversation_id': 1}},
            {'key': {'admin_id': 1}},
            {'key': {'language': 1}},
            {'key': {'improvement_category': 1}},
            {'key': {'applied_to_training': 1}},
            {'key': {'created_at': 1}}
        ]
    }
}