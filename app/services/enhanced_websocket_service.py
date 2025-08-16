#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced WebSocket Service
Real-time messaging service with role-based access, internal messaging, and AI learning.
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import request, session
from flask_login import current_user
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from bson.objectid import ObjectId

from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import (
    ChatConversationV2, ChatMessageV2, AILearningData,
    MessageType, MessageVisibility, ConversationStatus, UserRole
)
from app.services.ai_service_manager import ai_service
from app.utils.chat_utils import get_system_prompt, detect_language

class EnhancedWebSocketChatService:
    """
    Enhanced WebSocket service for real-time chat with role-based access and internal messaging.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        
        # Active connections tracking
        self.customer_sessions = {}  # session_id -> socket_info
        self.admin_sessions = {}     # admin_id -> socket_info
        self.socket_to_session = {}  # socket_id -> session_info
        
        # Admin rooms for internal communication
        self.admin_rooms = {
            'admin_general': 'admin_general',
            'super_admin_only': 'super_admin_only'
        }
        
        # Register event handlers
        self._register_events()
    
    def _register_events(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info(f"Client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info(f"Client disconnected: {request.sid}")
            self._handle_disconnect(request.sid)
        
        @self.socketio.on('customer_join')
        def handle_customer_join(data):
            self._handle_customer_join(data)
        
        @self.socketio.on('admin_join')
        def handle_admin_join(data):
            self._handle_admin_join(data)
        
        @self.socketio.on('customer_message')
        def handle_customer_message(data):
            self._handle_customer_message(data)
        
        @self.socketio.on('admin_message')
        def handle_admin_message(data):
            self._handle_admin_message(data)
        
        @self.socketio.on('internal_message')
        def handle_internal_message(data):
            self._handle_internal_message(data)
        
        @self.socketio.on('admin_takeover')
        def handle_admin_takeover(data):
            self._handle_admin_takeover(data)
        
        @self.socketio.on('admin_release')
        def handle_admin_release(data):
            self._handle_admin_release(data)
        
        @self.socketio.on('admin_correction')
        def handle_admin_correction(data):
            self._handle_admin_correction(data)
        
        @self.socketio.on('escalate_conversation')
        def handle_escalate_conversation(data):
            self._handle_escalate_conversation(data)
        
        @self.socketio.on('typing_start')
        def handle_typing_start(data):
            self._handle_typing_indicator(data, True)
        
        @self.socketio.on('typing_stop')
        def handle_typing_stop(data):
            self._handle_typing_indicator(data, False)
    
    def _handle_disconnect(self, socket_id: str):
        """Handle client disconnection."""
        try:
            if socket_id in self.socket_to_session:
                session_info = self.socket_to_session[socket_id]
                
                if session_info['type'] == 'customer':
                    session_id = session_info['session_id']
                    if session_id in self.customer_sessions:
                        del self.customer_sessions[session_id]
                    self._update_conversation_activity(session_id)
                    
                elif session_info['type'] == 'admin':
                    admin_id = session_info['admin_id']
                    if admin_id in self.admin_sessions:
                        del self.admin_sessions[admin_id]
                    self._update_admin_session_status(admin_id, 'offline')
                
                del self.socket_to_session[socket_id]
                
        except Exception as e:
            self.logger.error(f"Error handling disconnect: {e}")
    
    def _handle_customer_join(self, data: Dict[str, Any]):
        """Handle customer joining chat."""
        try:
            session_id = data.get('session_id') or str(uuid.uuid4())
            socket_id = request.sid
            
            # Store customer session
            self.customer_sessions[session_id] = {
                'socket_id': socket_id,
                'joined_at': datetime.utcnow(),
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr
            }
            
            self.socket_to_session[socket_id] = {
                'type': 'customer',
                'session_id': session_id
            }
            
            # Get or create conversation
            conversation = self._get_or_create_conversation(session_id, data)
            
            # Join customer to their conversation room
            join_room(f"conversation_{conversation.conversation_id}")
            
            # Send conversation history (filtered for customer view)
            history = self._get_conversation_history_for_role(
                conversation.conversation_id, UserRole.CUSTOMER.value
            )
            
            emit('conversation_joined', {
                'session_id': session_id,
                'conversation_id': conversation.conversation_id,
                'history': history
            })
            
            # Notify admins of new customer
            self._notify_admins_new_customer(conversation)
            
        except Exception as e:
            self.logger.error(f"Error handling customer join: {e}")
            emit('error', {'message': 'Failed to join chat'})
    
    def _handle_admin_join(self, data: Dict[str, Any]):
        """Handle admin joining chat system."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            admin_id = str(current_user.get_id())
            socket_id = request.sid
            
            # Store admin session
            self.admin_sessions[admin_id] = {
                'socket_id': socket_id,
                'admin_name': current_user.full_name,
                'admin_role': admin_role,
                'joined_at': datetime.utcnow(),
                'active_conversations': []
            }
            
            self.socket_to_session[socket_id] = {
                'type': 'admin',
                'admin_id': admin_id,
                'admin_role': admin_role
            }
            
            # Join admin rooms based on role
            join_room(self.admin_rooms['admin_general'])
            if admin_role == UserRole.SUPER_ADMIN.value:
                join_room(self.admin_rooms['super_admin_only'])
            
            # Update admin session status
            self._update_admin_session_status(admin_id, 'online')
            
            # Send active conversations
            conversations = self._get_active_conversations_for_admin(admin_role)
            
            emit('admin_joined', {
                'admin_id': admin_id,
                'admin_role': admin_role,
                'active_conversations': conversations
            })
            
        except Exception as e:
            self.logger.error(f"Error handling admin join: {e}")
            emit('error', {'message': 'Failed to join admin chat'})
    
    def _handle_customer_message(self, data: Dict[str, Any]):
        """Handle customer message."""
        try:
            session_id = data.get('session_id')
            message_content = data.get('message', '').strip()
            
            if not session_id or not message_content:
                emit('error', {'message': 'Session ID and message are required'})
                return
            
            # Get conversation
            conversation = self._get_conversation_by_session(session_id)
            if not conversation:
                emit('error', {'message': 'Conversation not found'})
                return
            
            # Create customer message
            customer_message = ChatMessageV2({
                'conversation_id': conversation.conversation_id,
                'session_id': session_id,
                'message_type': MessageType.USER.value,
                'content': message_content,
                'timestamp': datetime.utcnow(),
                'visibility': MessageVisibility.PUBLIC.value,
                'sender_role': UserRole.CUSTOMER.value,
                'sender_ip': request.remote_addr,
                'language_detected': detect_language(message_content)
            })
            
            # Save message
            message_id = self._save_message(customer_message)
            customer_message._id = message_id
            
            # Emit to conversation room (visible to customer and admins)
            self.socketio.emit('new_message', {
                'message': self._format_message_for_role(customer_message, UserRole.CUSTOMER.value),
                'conversation_id': conversation.conversation_id
            }, room=f"conversation_{conversation.conversation_id}")
            
            # Check if admin has taken over
            if conversation.is_admin_active:
                # Notify admin of customer message
                self._notify_admin_of_customer_message(conversation.admin_taken_by, customer_message)
            else:
                # Generate AI response
                self._generate_ai_response(conversation, customer_message)
            
            # Update conversation activity
            self._update_conversation_activity(session_id)
            
        except Exception as e:
            self.logger.error(f"Error handling customer message: {e}")
            emit('error', {'message': 'Failed to send message'})
    
    def _handle_admin_message(self, data: Dict[str, Any]):
        """Handle admin message to customer."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            conversation_id = data.get('conversation_id')
            message_content = data.get('message', '').strip()
            appears_as_ai = data.get('appears_as_ai', True)  # Default: appear as AI to customer
            
            if not conversation_id or not message_content:
                emit('error', {'message': 'Conversation ID and message are required'})
                return
            
            # Get conversation
            conversation = self._get_conversation_by_id(conversation_id)
            if not conversation:
                emit('error', {'message': 'Conversation not found'})
                return
            
            # Create admin message
            admin_message = ChatMessageV2({
                'conversation_id': conversation_id,
                'session_id': conversation.session_id,
                'message_type': MessageType.AI.value if appears_as_ai else MessageType.ADMIN.value,
                'content': message_content,
                'timestamp': datetime.utcnow(),
                'visibility': MessageVisibility.PUBLIC.value,
                'sender_id': ObjectId(current_user.get_id()),
                'sender_name': current_user.full_name,
                'sender_role': admin_role,
                'is_admin_message': True,
                'admin_id': ObjectId(current_user.get_id()),
                'appears_as_ai': appears_as_ai,
                'language_detected': detect_language(message_content)
            })
            
            # Save message
            message_id = self._save_message(admin_message)
            admin_message._id = message_id
            
            # Emit to customer (appears as AI if configured)
            customer_message = self._format_message_for_role(admin_message, UserRole.CUSTOMER.value)
            self.socketio.emit('new_message', {
                'message': customer_message,
                'conversation_id': conversation_id
            }, room=f"conversation_{conversation_id}")
            
            # Emit to admins (shows true admin message)
            admin_message_formatted = self._format_message_for_role(admin_message, UserRole.ADMIN.value)
            self.socketio.emit('admin_message_sent', {
                'message': admin_message_formatted,
                'conversation_id': conversation_id
            }, room=self.admin_rooms['admin_general'])
            
            # Update conversation activity
            self._update_conversation_activity(conversation.session_id)
            
        except Exception as e:
            self.logger.error(f"Error handling admin message: {e}")
            emit('error', {'message': 'Failed to send admin message'})
    
    def _handle_internal_message(self, data: Dict[str, Any]):
        """Handle internal admin-only message."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            conversation_id = data.get('conversation_id')
            message_content = data.get('message', '').strip()
            internal_tags = data.get('tags', [])
            visibility = data.get('visibility', MessageVisibility.ADMIN_ONLY.value)
            
            if not conversation_id or not message_content:
                emit('error', {'message': 'Conversation ID and message are required'})
                return
            
            # Validate visibility based on admin role
            if visibility == MessageVisibility.SUPER_ADMIN_ONLY.value and admin_role != UserRole.SUPER_ADMIN.value:
                emit('error', {'message': 'Super admin access required for this visibility level'})
                return
            
            # Create internal message
            internal_message = ChatMessageV2({
                'conversation_id': conversation_id,
                'message_type': MessageType.INTERNAL.value,
                'content': message_content,
                'timestamp': datetime.utcnow(),
                'visibility': visibility,
                'is_internal': True,
                'sender_id': ObjectId(current_user.get_id()),
                'sender_name': current_user.full_name,
                'sender_role': admin_role,
                'internal_tags': internal_tags,
                'visible_to_roles': self._get_visible_roles_for_visibility(visibility)
            })
            
            # Save message
            message_id = self._save_message(internal_message)
            internal_message._id = message_id
            
            # Emit only to appropriate admin rooms
            target_room = self.admin_rooms['admin_general']
            if visibility == MessageVisibility.SUPER_ADMIN_ONLY.value:
                target_room = self.admin_rooms['super_admin_only']
            
            self.socketio.emit('internal_message', {
                'message': self._format_message_for_role(internal_message, admin_role),
                'conversation_id': conversation_id
            }, room=target_room)
            
            # Update conversation internal message count
            mongo_db.db.chat_conversations_v2.update_one(
                {'conversation_id': conversation_id},
                {'$inc': {'total_internal_messages': 1}}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling internal message: {e}")
            emit('error', {'message': 'Failed to send internal message'})
    
    def _handle_admin_correction(self, data: Dict[str, Any]):
        """Handle admin correction of AI response for learning."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            conversation_id = data.get('conversation_id')
            original_message_id = data.get('original_message_id')
            corrected_response = data.get('corrected_response', '').strip()
            correction_reason = data.get('correction_reason', '')
            improvement_category = data.get('improvement_category', '')
            
            if not all([conversation_id, original_message_id, corrected_response]):
                emit('error', {'message': 'Missing required fields for correction'})
                return
            
            # Get the original AI message to correct
            original_message = mongo_db.db.chat_messages_v2.find_one({
                '_id': ObjectId(original_message_id),
                'conversation_id': conversation_id,
                'message_type': MessageType.AI.value
            })
            
            if not original_message:
                emit('error', {'message': 'Original AI message not found'})
                return
            
            # Get the customer message that prompted the AI response
            customer_message = mongo_db.db.chat_messages_v2.find_one({
                'conversation_id': conversation_id,
                'timestamp': {'$lt': original_message['timestamp']},
                'message_type': MessageType.USER.value
            }, sort=[('timestamp', -1)])
            
            # Create AI learning data
            learning_data = AILearningData({
                'conversation_id': conversation_id,
                'original_message': customer_message['content'] if customer_message else '',
                'ai_response': original_message['content'],
                'admin_correction': corrected_response,
                'correction_reason': correction_reason,
                'improvement_category': improvement_category,
                'language': original_message.get('language_detected', 'en'),
                'admin_id': ObjectId(current_user.get_id()),
                'admin_name': current_user.full_name,
                'confidence_before': original_message.get('ai_confidence', 0.0)
            })
            
            # Save learning data
            mongo_db.db.ai_learning_data.insert_one(learning_data.to_dict())
            
            # Update original message with correction info
            mongo_db.db.chat_messages_v2.update_one(
                {'_id': ObjectId(original_message_id)},
                {
                    '$set': {
                        'admin_correction': corrected_response,
                        'correction_reason': correction_reason,
                        'admin_override': True,
                        'is_training_data': True,
                        'edited': True,
                        'edited_at': datetime.utcnow(),
                        'edited_by': ObjectId(current_user.get_id())
                    }
                }
            )
            
            # Update conversation correction count
            mongo_db.db.chat_conversations_v2.update_one(
                {'conversation_id': conversation_id},
                {'$inc': {'admin_corrections_count': 1}}
            )
            
            # Send corrected message to customer
            corrected_message = ChatMessageV2({
                'conversation_id': conversation_id,
                'message_type': MessageType.AI.value,
                'content': corrected_response,
                'timestamp': datetime.utcnow(),
                'visibility': MessageVisibility.PUBLIC.value,
                'sender_role': UserRole.ADMIN.value,
                'is_admin_message': True,
                'admin_id': ObjectId(current_user.get_id()),
                'appears_as_ai': True,
                'admin_override': True
            })
            
            # Save corrected message
            corrected_message_id = self._save_message(corrected_message)
            corrected_message._id = corrected_message_id
            
            # Emit corrected message to customer
            self.socketio.emit('message_corrected', {
                'original_message_id': original_message_id,
                'corrected_message': self._format_message_for_role(corrected_message, UserRole.CUSTOMER.value),
                'conversation_id': conversation_id
            }, room=f"conversation_{conversation_id}")
            
            # Notify admins of correction
            self.socketio.emit('admin_correction_made', {
                'conversation_id': conversation_id,
                'admin_name': current_user.full_name,
                'correction_reason': correction_reason,
                'improvement_category': improvement_category
            }, room=self.admin_rooms['admin_general'])
            
        except Exception as e:
            self.logger.error(f"Error handling admin correction: {e}")
            emit('error', {'message': 'Failed to process correction'})
    
    def _handle_admin_takeover(self, data: Dict[str, Any]):
        """Handle admin takeover of conversation."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                emit('error', {'message': 'Conversation ID required'})
                return
            
            # Update conversation
            result = mongo_db.db.chat_conversations_v2.update_one(
                {
                    'conversation_id': conversation_id,
                    'is_admin_active': False  # Only take over if not already taken
                },
                {
                    '$set': {
                        'is_admin_active': True,
                        'admin_taken_by': ObjectId(current_user.get_id()),
                        'admin_taken_at': datetime.utcnow(),
                        'status': ConversationStatus.ADMIN_TAKEN.value
                    }
                }
            )
            
            if result.modified_count == 0:
                emit('error', {'message': 'Conversation already taken or not found'})
                return
            
            # Join admin to conversation room
            join_room(f"conversation_{conversation_id}")
            
            # Notify other admins
            self.socketio.emit('conversation_taken_over', {
                'conversation_id': conversation_id,
                'admin_name': current_user.full_name,
                'admin_id': str(current_user.get_id())
            }, room=self.admin_rooms['admin_general'])
            
            emit('takeover_success', {
                'conversation_id': conversation_id,
                'message': 'Conversation taken over successfully'
            })
            
        except Exception as e:
            self.logger.error(f"Error handling admin takeover: {e}")
            emit('error', {'message': 'Failed to take over conversation'})
    
    def _handle_admin_release(self, data: Dict[str, Any]):
        """Handle admin release of conversation."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                emit('error', {'message': 'Conversation ID required'})
                return
            
            # Update conversation
            result = mongo_db.db.chat_conversations_v2.update_one(
                {
                    'conversation_id': conversation_id,
                    'admin_taken_by': ObjectId(current_user.get_id())
                },
                {
                    '$set': {
                        'is_admin_active': False,
                        'status': ConversationStatus.ACTIVE.value
                    },
                    '$unset': {
                        'admin_taken_by': '',
                        'admin_taken_at': ''
                    }
                }
            )
            
            if result.modified_count == 0:
                emit('error', {'message': 'Conversation not found or not taken by you'})
                return
            
            # Leave conversation room
            leave_room(f"conversation_{conversation_id}")
            
            # Notify other admins
            self.socketio.emit('conversation_released', {
                'conversation_id': conversation_id,
                'admin_name': current_user.full_name
            }, room=self.admin_rooms['admin_general'])
            
            emit('release_success', {
                'conversation_id': conversation_id,
                'message': 'Conversation released successfully'
            })
            
        except Exception as e:
            self.logger.error(f"Error handling admin release: {e}")
            emit('error', {'message': 'Failed to release conversation'})
    
    def _handle_escalate_conversation(self, data: Dict[str, Any]):
        """Handle conversation escalation."""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                return
            
            admin_role = self._get_user_role(current_user)
            if admin_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                emit('error', {'message': 'Admin access required'})
                return
            
            conversation_id = data.get('conversation_id')
            escalation_reason = data.get('reason', '')
            priority_level = data.get('priority_level', 'high')
            
            if not conversation_id:
                emit('error', {'message': 'Conversation ID required'})
                return
            
            # Update conversation
            mongo_db.db.chat_conversations_v2.update_one(
                {'conversation_id': conversation_id},
                {
                    '$set': {
                        'status': ConversationStatus.ESCALATED.value,
                        'priority_level': priority_level,
                        'escalation_level': 1
                    },
                    '$push': {
                        'admin_notes': {
                            'type': 'escalation',
                            'reason': escalation_reason,
                            'admin_id': ObjectId(current_user.get_id()),
                            'admin_name': current_user.full_name,
                            'timestamp': datetime.utcnow()
                        }
                    }
                }
            )
            
            # Create escalation message
            escalation_message = ChatMessageV2({
                'conversation_id': conversation_id,
                'message_type': MessageType.SYSTEM.value,
                'content': f"Conversation escalated by {current_user.full_name}. Reason: {escalation_reason}",
                'timestamp': datetime.utcnow(),
                'visibility': MessageVisibility.ADMIN_ONLY.value,
                'is_internal': True,
                'sender_id': ObjectId(current_user.get_id()),
                'sender_role': admin_role,
                'escalation_flag': True
            })
            
            # Save escalation message
            self._save_message(escalation_message)
            
            # Notify super admins
            self.socketio.emit('conversation_escalated', {
                'conversation_id': conversation_id,
                'escalated_by': current_user.full_name,
                'reason': escalation_reason,
                'priority_level': priority_level
            }, room=self.admin_rooms['super_admin_only'])
            
            emit('escalation_success', {
                'conversation_id': conversation_id,
                'message': 'Conversation escalated successfully'
            })
            
        except Exception as e:
            self.logger.error(f"Error handling conversation escalation: {e}")
            emit('error', {'message': 'Failed to escalate conversation'})
    
    def _handle_typing_indicator(self, data: Dict[str, Any], is_typing: bool):
        """Handle typing indicators."""
        try:
            session_id = data.get('session_id')
            conversation_id = data.get('conversation_id')
            
            if session_id:
                # Customer typing
                self.socketio.emit('customer_typing', {
                    'session_id': session_id,
                    'is_typing': is_typing
                }, room=self.admin_rooms['admin_general'])
            
            elif conversation_id and current_user.is_authenticated:
                # Admin typing
                admin_role = self._get_user_role(current_user)
                if admin_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
                    self.socketio.emit('admin_typing', {
                        'conversation_id': conversation_id,
                        'admin_name': current_user.full_name,
                        'is_typing': is_typing
                    }, room=f"conversation_{conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling typing indicator: {e}")
    
    def _generate_ai_response(self, conversation: ChatConversationV2, customer_message: ChatMessageV2):
        """Generate AI response to customer message."""
        try:
            # Get conversation context
            context_messages = self._get_conversation_context(conversation.conversation_id, limit=5)
            
            # Prepare system prompt
            system_prompt = get_system_prompt(customer_message.language_detected or 'en')
            
            # Get AI response
            ai_response = ai_service.get_ai_response(
                message=customer_message.content,
                language=customer_message.language_detected or 'en',
                system_prompt=system_prompt,
                context={'conversation_history': context_messages}
            )
            
            if ai_response and ai_response.content:
                # Create AI message
                ai_message = ChatMessageV2({
                    'conversation_id': conversation.conversation_id,
                    'session_id': conversation.session_id,
                    'message_type': MessageType.AI.value,
                    'content': ai_response.content,
                    'timestamp': datetime.utcnow(),
                    'visibility': MessageVisibility.PUBLIC.value,
                    'ai_response_source': ai_response.source,
                    'ai_confidence': ai_response.confidence,
                    'ai_response_time_ms': ai_response.response_time_ms,
                    'ai_model_used': 'gpt-4o-mini',
                    'language_detected': customer_message.language_detected
                })
                
                # Save AI message
                message_id = self._save_message(ai_message)
                ai_message._id = message_id
                
                # Emit AI response to conversation room
                self.socketio.emit('new_message', {
                    'message': self._format_message_for_role(ai_message, UserRole.CUSTOMER.value),
                    'conversation_id': conversation.conversation_id
                }, room=f"conversation_{conversation.conversation_id}")
                
            else:
                # Send fallback response
                self._send_fallback_response(conversation)
                
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            self._send_fallback_response(conversation)
    
    def _send_fallback_response(self, conversation: ChatConversationV2):
        """Send fallback response when AI fails."""
        fallback_message = ChatMessageV2({
            'conversation_id': conversation.conversation_id,
            'session_id': conversation.session_id,
            'message_type': MessageType.AI.value,
            'content': "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.PUBLIC.value,
            'ai_response_source': 'fallback'
        })
        
        message_id = self._save_message(fallback_message)
        fallback_message._id = message_id
        
        self.socketio.emit('new_message', {
            'message': self._format_message_for_role(fallback_message, UserRole.CUSTOMER.value),
            'conversation_id': conversation.conversation_id
        }, room=f"conversation_{conversation.conversation_id}")
    
    # Helper methods
    def _get_user_role(self, user) -> str:
        """Get user role from user object."""
        if hasattr(user, 'role'):
            if user.role == 'super_admin':
                return UserRole.SUPER_ADMIN.value
            elif user.role in ['admin', 'sub_admin']:
                return UserRole.ADMIN.value
        return UserRole.USER.value
    
    def _get_visible_roles_for_visibility(self, visibility: str) -> List[str]:
        """Get list of roles that can see a message with given visibility."""
        if visibility == MessageVisibility.PUBLIC.value:
            return [UserRole.CUSTOMER.value, UserRole.USER.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        elif visibility == MessageVisibility.ADMIN_ONLY.value:
            return [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        elif visibility == MessageVisibility.INTERNAL.value:
            return [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        elif visibility == MessageVisibility.SUPER_ADMIN_ONLY.value:
            return [UserRole.SUPER_ADMIN.value]
        return []
    
    def _format_message_for_role(self, message: ChatMessageV2, user_role: str) -> Dict:
        """Format message based on user role visibility."""
        if not message.is_visible_to_role(user_role):
            return None
        
        formatted = {
            'id': str(message._id),
            'content': message.content,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'message_type': message.message_type
        }
        
        # Add role-specific information
        if user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            formatted.update({
                'visibility': message.visibility,
                'is_internal': message.is_internal,
                'sender_role': message.sender_role,
                'sender_name': message.sender_name,
                'is_admin_message': message.is_admin_message,
                'appears_as_ai': message.appears_as_ai,
                'admin_override': message.admin_override,
                'ai_confidence': message.ai_confidence,
                'internal_tags': message.internal_tags,
                'escalation_flag': message.escalation_flag
            })
        
        return formatted
    
    def _get_conversation_history_for_role(self, conversation_id: str, user_role: str) -> List[Dict]:
        """Get conversation history filtered by user role."""
        try:
            messages_cursor = mongo_db.db.chat_messages_v2.find({
                'conversation_id': conversation_id
            }).sort('timestamp', 1)
            
            history = []
            for msg_doc in messages_cursor:
                message = ChatMessageV2(msg_doc)
                formatted_message = self._format_message_for_role(message, user_role)
                if formatted_message:
                    history.append(formatted_message)
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _get_or_create_conversation(self, session_id: str, data: Dict[str, Any]) -> ChatConversationV2:
        """Get existing conversation or create new one."""
        try:
            # Try to find existing conversation
            conv_data = mongo_db.db.chat_conversations_v2.find_one({
                'session_id': session_id
            })
            
            if conv_data:
                return ChatConversationV2(conv_data)
            
            # Create new conversation
            conversation = ChatConversationV2({
                'conversation_id': str(uuid.uuid4()),
                'session_id': session_id,
                'customer_ip': request.remote_addr,
                'customer_user_agent': request.headers.get('User-Agent', ''),
                'status': ConversationStatus.ACTIVE.value,
                'language_detected': data.get('language', 'en')
            })
            
            # Save to database
            result = mongo_db.db.chat_conversations_v2.insert_one(conversation.to_dict())
            conversation._id = result.inserted_id
            
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error getting/creating conversation: {e}")
            raise
    
    def _get_conversation_by_session(self, session_id: str) -> Optional[ChatConversationV2]:
        """Get conversation by session ID."""
        try:
            conv_data = mongo_db.db.chat_conversations_v2.find_one({
                'session_id': session_id
            })
            return ChatConversationV2(conv_data) if conv_data else None
        except Exception as e:
            self.logger.error(f"Error getting conversation by session: {e}")
            return None
    
    def _get_conversation_by_id(self, conversation_id: str) -> Optional[ChatConversationV2]:
        """Get conversation by ID."""
        try:
            conv_data = mongo_db.db.chat_conversations_v2.find_one({
                'conversation_id': conversation_id
            })
            return ChatConversationV2(conv_data) if conv_data else None
        except Exception as e:
            self.logger.error(f"Error getting conversation by ID: {e}")
            return None
    
    def _get_conversation_context(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation context for AI."""
        try:
            messages_cursor = mongo_db.db.chat_messages_v2.find({
                'conversation_id': conversation_id,
                'visibility': MessageVisibility.PUBLIC.value
            }).sort('timestamp', -1).limit(limit)
            
            context = []
            for msg_doc in reversed(list(messages_cursor)):
                context.append({
                    'role': 'user' if msg_doc['message_type'] == MessageType.USER.value else 'assistant',
                    'content': msg_doc['content']
                })
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting conversation context: {e}")
            return []
    
    def _get_active_conversations_for_admin(self, admin_role: str) -> List[Dict]:
        """Get active conversations for admin dashboard."""
        try:
            since = datetime.utcnow() - timedelta(hours=24)
            
            conversations_cursor = mongo_db.db.chat_conversations_v2.find({
                'status': {'$in': [ConversationStatus.ACTIVE.value, ConversationStatus.ADMIN_TAKEN.value, ConversationStatus.ESCALATED.value]},
                'last_activity': {'$gte': since}
            }).sort('last_activity', -1)
            
            conversations = []
            for conv_data in conversations_cursor:
                conversation = ChatConversationV2(conv_data)
                conversations.append({
                    'conversation_id': conversation.conversation_id,
                    'session_id': conversation.session_id,
                    'status': conversation.status,
                    'is_admin_active': conversation.is_admin_active,
                    'admin_taken_by': str(conversation.admin_taken_by) if conversation.admin_taken_by else None,
                    'created_at': conversation.created_at.isoformat(),
                    'last_activity': conversation.last_activity.isoformat(),
                    'total_messages': conversation.total_messages,
                    'total_internal_messages': conversation.total_internal_messages,
                    'priority_level': conversation.priority_level,
                    'escalation_level': conversation.escalation_level
                })
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"Error getting active conversations: {e}")
            return []
    
    def _save_message(self, message: ChatMessageV2) -> ObjectId:
        """Save message to database."""
        try:
            result = mongo_db.db.chat_messages_v2.insert_one(message.to_dict())
            
            # Update conversation message count
            update_data = {'$inc': {'total_messages': 1}, '$set': {'last_activity': datetime.utcnow()}}
            if message.is_internal:
                update_data['$inc']['total_internal_messages'] = 1
            
            mongo_db.db.chat_conversations_v2.update_one(
                {'conversation_id': message.conversation_id},
                update_data
            )
            
            return result.inserted_id
            
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            raise
    
    def _update_conversation_activity(self, session_id: str):
        """Update conversation last activity."""
        try:
            mongo_db.db.chat_conversations_v2.update_one(
                {'session_id': session_id},
                {'$set': {'last_activity': datetime.utcnow()}}
            )
        except Exception as e:
            self.logger.error(f"Error updating conversation activity: {e}")
    
    def _update_admin_session_status(self, admin_id: str, status: str):
        """Update admin session status."""
        try:
            mongo_db.db.admin_sessions.update_one(
                {'admin_id': ObjectId(admin_id)},
                {
                    '$set': {
                        'status': status,
                        'last_seen': datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Error updating admin session status: {e}")
    
    def _notify_admins_new_customer(self, conversation: ChatConversationV2):
        """Notify admins of new customer conversation."""
        try:
            self.socketio.emit('new_customer_conversation', {
                'conversation_id': conversation.conversation_id,
                'session_id': conversation.session_id,
                'created_at': conversation.created_at.isoformat(),
                'language_detected': conversation.language_detected
            }, room=self.admin_rooms['admin_general'])
        except Exception as e:
            self.logger.error(f"Error notifying admins of new customer: {e}")
    
    def _notify_admin_of_customer_message(self, admin_id: ObjectId, message: ChatMessageV2):
        """Notify specific admin of customer message."""
        try:
            if str(admin_id) in self.admin_sessions:
                admin_socket = self.admin_sessions[str(admin_id)]['socket_id']
                self.socketio.emit('customer_message_for_admin', {
                    'message': self._format_message_for_role(message, UserRole.ADMIN.value),
                    'conversation_id': str(message.conversation_id)
                }, room=admin_socket)
        except Exception as e:
            self.logger.error(f"Error notifying admin of customer message: {e}")

# Global service instance
enhanced_websocket_service = None

def init_enhanced_websocket_service(socketio: SocketIO):
    """Initialize the enhanced WebSocket service."""
    global enhanced_websocket_service
    enhanced_websocket_service = EnhancedWebSocketChatService(socketio)
    return enhanced_websocket_service