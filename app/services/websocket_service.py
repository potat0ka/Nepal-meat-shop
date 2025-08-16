#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - WebSocket Service
Real-time messaging service for customer-admin chat with takeover functionality.
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
from app.models.enhanced_chat import (
    ChatConversation, ChatMessage, AdminSession,
    MessageType, ConversationStatus, AdminSessionStatus
)
from app.services.ai_service_manager import ai_service
from app.services.chat_takeover_service import chat_takeover_service
from app.utils.chat_utils import get_system_prompt, detect_language

class WebSocketChatService:
    """
    WebSocket service for real-time chat functionality.
    Handles customer-admin communication with AI integration.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.logger = logging.getLogger(__name__)
        
        # Active connections tracking
        self.customer_sessions = {}  # session_id -> socket_id
        self.admin_sessions = {}     # admin_id -> socket_id
        self.socket_to_session = {}  # socket_id -> session_info
        
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
        
        @self.socketio.on('admin_takeover')
        def handle_admin_takeover(data):
            self._handle_admin_takeover(data)
        
        @self.socketio.on('admin_release')
        def handle_admin_release(data):
            self._handle_admin_release(data)
        
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
                    
                    # Update conversation status
                    self._update_conversation_activity(session_id)
                
                elif session_info['type'] == 'admin':
                    admin_id = session_info['admin_id']
                    if admin_id in self.admin_sessions:
                        del self.admin_sessions[admin_id]
                    
                    # Update admin session status
                    self._update_admin_session_status(admin_id, AdminSessionStatus.OFFLINE.value)
                
                del self.socket_to_session[socket_id]
        
        except Exception as e:
            self.logger.error(f"Error handling disconnect: {e}")
    
    def _handle_customer_join(self, data: Dict[str, Any]):
        """Handle customer joining chat."""
        try:
            session_id = data.get('session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Store customer session
            self.customer_sessions[session_id] = request.sid
            self.socket_to_session[request.sid] = {
                'type': 'customer',
                'session_id': session_id,
                'user_id': current_user.get_id() if current_user.is_authenticated else None
            }
            
            # Join customer room
            join_room(f"customer_{session_id}")
            
            # Get or create conversation
            conversation = self._get_or_create_conversation(session_id, data)
            
            # Load chat history
            messages = self._get_conversation_messages(conversation.id)
            
            # Send session info and history to customer
            emit('session_established', {
                'session_id': session_id,
                'conversation_id': conversation.id,
                'messages': [msg.to_json_dict() for msg in messages]
            })
            
            self.logger.info(f"Customer joined: session_id={session_id}, socket_id={request.sid}")
        
        except Exception as e:
            self.logger.error(f"Error handling customer join: {e}")
            emit('error', {'message': 'Failed to join chat'})
    
    def _handle_admin_join(self, data: Dict[str, Any]):
        """Handle admin joining chat system."""
        try:
            if not current_user.is_authenticated or current_user.role not in ['admin', 'sub_admin']:
                emit('error', {'message': 'Unauthorized'})
                return
            
            admin_id = current_user.get_id()
            
            # Store admin session
            self.admin_sessions[admin_id] = request.sid
            self.socket_to_session[request.sid] = {
                'type': 'admin',
                'admin_id': admin_id,
                'admin_name': current_user.full_name or current_user.username
            }
            
            # Join admin room
            join_room("admin_panel")
            
            # Update admin session in database
            self._update_admin_session(admin_id, request.sid)
            
            # Send active conversations to admin
            active_conversations = self._get_active_conversations()
            emit('admin_dashboard', {
                'conversations': [conv.to_json_dict() for conv in active_conversations]
            })
            
            self.logger.info(f"Admin joined: admin_id={admin_id}, socket_id={request.sid}")
        
        except Exception as e:
            self.logger.error(f"Error handling admin join: {e}")
            emit('error', {'message': 'Failed to join admin panel'})
    
    def _handle_customer_message(self, data: Dict[str, Any]):
        """Handle customer message - route to admin if taken over, otherwise to AI."""
        try:
            session_id = data.get('session_id')
            message_content = data.get('message', '').strip()
            chat_mode = data.get('mode', 'message')  # 'message' or 'reply'
            reply_to_message = data.get('reply_to_message')  # For reply mode
            
            if not session_id or not message_content:
                emit('error', {'message': 'Invalid message data'})
                return
            
            # Get conversation
            conversation = self._get_conversation_by_session(session_id)
            if not conversation:
                emit('error', {'message': 'Conversation not found'})
                return
            
            # Create customer message
            customer_message = ChatMessage({
                'conversation_id': ObjectId(conversation.id),
                'session_id': session_id,
                'message_type': MessageType.USER.value,
                'content': message_content,
                'sender_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None,
                'sender_ip': request.remote_addr,
                'timestamp': datetime.utcnow(),
                'chat_mode': chat_mode,
                'reply_to_message': reply_to_message
            })
            
            # Save customer message
            message_id = self._save_message(customer_message)
            customer_message._id = message_id
            
            # Emit message to customer
            emit('message_received', customer_message.to_json_dict())
            
            # Use takeover service to determine routing
            routing_info = chat_takeover_service.handle_customer_message(
                conversation.id, message_content, session_id
            )
            
            # Notify admins about new message with routing info
            self.socketio.emit('new_customer_message', {
                'conversation_id': conversation.id,
                'session_id': session_id,
                'message': customer_message.to_json_dict(),
                'routing_info': routing_info
            }, room="admin_panel")
            
            # Route based on takeover status
            if routing_info['route_to'] == 'admin':
                # Admin has taken over - notify admin and wait for response
                admin_info = routing_info['admin_info']
                self.socketio.emit('admin_response_required', {
                    'conversation_id': conversation.id,
                    'session_id': session_id,
                    'message': customer_message.to_json_dict(),
                    'admin_id': admin_info['admin_id'],
                    'admin_name': admin_info['admin_name']
                }, room=f"admin_{admin_info['admin_id']}")
            else:
                # Generate AI response
                self._generate_ai_response(conversation, customer_message)
            
            # Update conversation activity
            self._update_conversation_activity(session_id)
        
        except Exception as e:
            self.logger.error(f"Error handling customer message: {e}")
            emit('error', {'message': 'Failed to send message'})
    
    def _handle_admin_message(self, data: Dict[str, Any]):
        """Handle admin message."""
        try:
            if not current_user.is_authenticated or current_user.role not in ['admin', 'sub_admin']:
                emit('error', {'message': 'Unauthorized'})
                return
            
            conversation_id = data.get('conversation_id')
            message_content = data.get('message', '').strip()
            appears_as_ai = data.get('appears_as_ai', True)  # Default to appearing as AI
            
            if not conversation_id or not message_content:
                emit('error', {'message': 'Invalid message data'})
                return
            
            # Check if admin has takeover for this conversation
            if not chat_takeover_service.is_conversation_taken_by_admin(conversation_id, current_user.get_id()):
                emit('error', {'message': 'You must take over the conversation first'})
                return
            
            # Use chat takeover service to send admin message
            success = chat_takeover_service.send_admin_message(
                conversation_id=conversation_id,
                admin_id=current_user.get_id(),
                message_content=message_content,
                appears_as_ai=appears_as_ai
            )
            
            if success:
                # Get the saved message for broadcasting
                conversation = self._get_conversation_by_id(conversation_id)
                if conversation:
                    # Create message data for customer (appears as AI)
                    customer_message_data = {
                        'conversation_id': conversation_id,
                        'session_id': conversation.session_id,
                        'message_type': MessageType.AI.value,
                        'content': message_content,
                        'timestamp': datetime.utcnow().isoformat(),
                        'is_admin_message': False  # Hide admin nature from customer
                    }
                    
                    # Send to customer as AI message
                    self.socketio.emit('message_received', customer_message_data, 
                                     room=f"customer_{conversation.session_id}")
                    
                    # Send confirmation to admin with full details
                    admin_message_data = {
                        'conversation_id': conversation_id,
                        'session_id': conversation.session_id,
                        'message_type': MessageType.ADMIN.value,
                        'content': message_content,
                        'sender_id': current_user.get_id(),
                        'sender_name': current_user.full_name or current_user.username,
                        'is_admin_message': True,
                        'appears_as_ai': appears_as_ai,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    emit('message_sent', admin_message_data)
                    
                    # Update conversation activity
                    self._update_conversation_activity(conversation.session_id)
            else:
                emit('error', {'message': 'Failed to send message'})
        
        except Exception as e:
            self.logger.error(f"Error handling admin message: {e}")
            emit('error', {'message': 'Failed to send message'})
    
    def _handle_admin_takeover(self, data: Dict[str, Any]):
        """Handle admin taking over a conversation."""
        try:
            if not current_user.is_authenticated or current_user.role not in ['admin', 'sub_admin']:
                emit('error', {'message': 'Unauthorized'})
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                emit('error', {'message': 'Invalid conversation ID'})
                return
            
            # Use chat takeover service for silent takeover
            success = chat_takeover_service.request_takeover(
                conversation_id=conversation_id,
                admin_id=current_user.get_id()
            )
            
            if success:
                # Join admin to conversation room
                join_room(f"admin_conv_{conversation_id}")
                
                # Notify other admins
                self.socketio.emit('conversation_taken', {
                    'conversation_id': conversation_id,
                    'admin_name': current_user.full_name or current_user.username
                }, room="admin_panel")
                
                emit('takeover_success', {'conversation_id': conversation_id})
                
                self.logger.info(f"Admin {current_user.get_id()} took over conversation {conversation_id}")
            else:
                emit('error', {'message': 'Failed to take over conversation'})
        
        except Exception as e:
            self.logger.error(f"Error handling admin takeover: {e}")
            emit('error', {'message': 'Failed to take over conversation'})
    
    def _handle_admin_release(self, data: Dict[str, Any]):
        """Handle admin releasing a conversation back to AI."""
        try:
            if not current_user.is_authenticated or current_user.role not in ['admin', 'sub_admin']:
                emit('error', {'message': 'Unauthorized'})
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                emit('error', {'message': 'Invalid conversation ID'})
                return
            
            # Use chat takeover service for silent release
            success = chat_takeover_service.release_takeover(
                conversation_id=conversation_id,
                admin_id=current_user.get_id()
            )
            
            if success:
                # Leave conversation room
                leave_room(f"admin_conv_{conversation_id}")
                
                # Notify other admins
                self.socketio.emit('conversation_released', {
                    'conversation_id': conversation_id,
                    'admin_name': current_user.full_name or current_user.username
                }, room="admin_panel")
                
                emit('release_success', {'conversation_id': conversation_id})
                
                self.logger.info(f"Admin {current_user.get_id()} released conversation {conversation_id}")
            else:
                emit('error', {'message': 'Failed to release conversation'})
        
        except Exception as e:
            self.logger.error(f"Error handling admin release: {e}")
            emit('error', {'message': 'Failed to release conversation'})
    
    def _handle_typing_indicator(self, data: Dict[str, Any], is_typing: bool):
        """Handle typing indicators."""
        try:
            if request.sid in self.socket_to_session:
                session_info = self.socket_to_session[request.sid]
                
                if session_info['type'] == 'customer':
                    session_id = session_info['session_id']
                    # Notify admins
                    self.socketio.emit('customer_typing', {
                        'session_id': session_id,
                        'is_typing': is_typing
                    }, room="admin_panel")
                
                elif session_info['type'] == 'admin':
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        conversation = self._get_conversation_by_id(conversation_id)
                        if conversation:
                            # Notify customer (but don't reveal it's admin typing)
                            self.socketio.emit('ai_typing', {
                                'is_typing': is_typing
                            }, room=f"customer_{conversation.session_id}")
        
        except Exception as e:
            self.logger.error(f"Error handling typing indicator: {e}")
    
    def _generate_ai_response(self, conversation: ChatConversation, customer_message: ChatMessage):
        """Generate AI response for customer message."""
        try:
            # Detect language
            language = detect_language(customer_message.content)
            
            # Get system prompt
            system_prompt = get_system_prompt(language)
            
            # Prepare context with chat mode information
            context = {
                'conversation_id': conversation.id,
                'chat_mode': getattr(customer_message, 'chat_mode', 'message'),
                'reply_to_message': getattr(customer_message, 'reply_to_message', None)
            }
            
            # If in reply mode, add context about what we're replying to
            if context['chat_mode'] == 'reply' and context['reply_to_message']:
                system_prompt += f"\n\nNote: The customer is replying to this previous message: '{context['reply_to_message']}'. Please respond appropriately to their reply."
            
            # Generate AI response
            ai_response = ai_service.get_ai_response(
                customer_message.content,
                language,
                system_prompt,
                context=context
            )
            
            # Create AI message
            ai_message = ChatMessage({
                'conversation_id': ObjectId(conversation.id),
                'session_id': conversation.session_id,
                'message_type': MessageType.AI.value,
                'content': ai_response.content,
                'ai_response_source': ai_response.source,
                'ai_confidence': ai_response.confidence,
                'ai_response_time_ms': ai_response.response_time_ms,
                'language_detected': language,
                'timestamp': datetime.utcnow()
            })
            
            # Save AI message
            message_id = self._save_message(ai_message)
            ai_message._id = message_id
            
            # Send AI response to customer
            self.socketio.emit('message_received', ai_message.to_json_dict(),
                             room=f"customer_{conversation.session_id}")
            
            # Notify admins
            self.socketio.emit('ai_response_sent', {
                'conversation_id': conversation.id,
                'message': ai_message.to_json_dict()
            }, room="admin_panel")
        
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            # Send fallback message
            self._send_fallback_response(conversation)
    
    def _send_fallback_response(self, conversation: ChatConversation):
        """Send fallback response when AI fails."""
        fallback_message = ChatMessage({
            'conversation_id': ObjectId(conversation.id),
            'session_id': conversation.session_id,
            'message_type': MessageType.AI.value,
            'content': "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or an admin will assist you shortly.",
            'ai_response_source': 'fallback',
            'timestamp': datetime.utcnow()
        })
        
        message_id = self._save_message(fallback_message)
        fallback_message._id = message_id
        
        self.socketio.emit('message_received', fallback_message.to_json_dict(),
                         room=f"customer_{conversation.session_id}")
    
    def _get_or_create_conversation(self, session_id: str, data: Dict[str, Any]) -> ChatConversation:
        """Get existing conversation or create new one."""
        # Try to find existing conversation
        conv_data = mongo_db.db.chat_conversations.find_one({'session_id': session_id})
        
        if conv_data:
            return ChatConversation(conv_data)
        
        # Create new conversation
        conversation_id = ObjectId()
        conversation_data = {
            '_id': conversation_id,
            'session_id': session_id,
            'customer_id': ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
            'customer_ip': request.remote_addr,
            'customer_user_agent': request.headers.get('User-Agent'),
            'status': ConversationStatus.ACTIVE.value,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'admin_taken_by': None,
            'admin_taken_at': None,
            'is_admin_active': False,
            'language_detected': 'en',
            'total_messages': 0,
            'customer_satisfaction': None,
            'tags': []
        }
        
        # Save to database first
        mongo_db.db.chat_conversations.insert_one(conversation_data)
        
        # Return conversation object
        return ChatConversation(conversation_data)
    
    def _get_conversation_by_session(self, session_id: str) -> Optional[ChatConversation]:
        """Get conversation by session ID."""
        conv_data = mongo_db.db.chat_conversations.find_one({'session_id': session_id})
        return ChatConversation(conv_data) if conv_data else None
    
    def _get_conversation_by_id(self, conversation_id: str) -> Optional[ChatConversation]:
        """Get conversation by ID."""
        conv_data = mongo_db.db.chat_conversations.find_one({'_id': ObjectId(conversation_id)})
        return ChatConversation(conv_data) if conv_data else None
    
    def _get_conversation_messages(self, conversation_id: str) -> List[ChatMessage]:
        """Get messages for a conversation."""
        messages_data = mongo_db.db.chat_messages.find(
            {'conversation_id': ObjectId(conversation_id)}
        ).sort('timestamp', 1)
        
        return [ChatMessage(msg_data) for msg_data in messages_data]
    
    def _get_active_conversations(self) -> List[ChatConversation]:
        """Get active conversations for admin dashboard."""
        conversations_data = mongo_db.db.chat_conversations.find({
            'status': {'$in': [ConversationStatus.ACTIVE.value, ConversationStatus.ADMIN_TAKEN.value]},
            'last_activity': {'$gte': datetime.utcnow() - timedelta(hours=24)}
        }).sort('last_activity', -1)
        
        return [ChatConversation(conv_data) for conv_data in conversations_data]
    
    def _save_message(self, message: ChatMessage) -> ObjectId:
        """Save message to database."""
        result = mongo_db.db.chat_messages.insert_one(message.to_dict())
        
        # Update conversation message count
        mongo_db.db.chat_conversations.update_one(
            {'_id': message.conversation_id},
            {
                '$inc': {'total_messages': 1},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        return result.inserted_id
    
    def _update_conversation_activity(self, session_id: str):
        """Update conversation last activity."""
        mongo_db.db.chat_conversations.update_one(
            {'session_id': session_id},
            {'$set': {'last_activity': datetime.utcnow(), 'updated_at': datetime.utcnow()}}
        )
    
    def _update_admin_session(self, admin_id: str, socket_id: str):
        """Update admin session in database."""
        mongo_db.db.admin_sessions.update_one(
            {'admin_id': ObjectId(admin_id)},
            {
                '$set': {
                    'socket_id': socket_id,
                    'status': AdminSessionStatus.ONLINE.value,
                    'last_seen': datetime.utcnow(),
                    'admin_name': current_user.full_name or current_user.username
                }
            },
            upsert=True
        )
    
    def _update_admin_session_status(self, admin_id: str, status: str):
        """Update admin session status."""
        mongo_db.db.admin_sessions.update_one(
            {'admin_id': ObjectId(admin_id)},
            {
                '$set': {
                    'status': status,
                    'last_seen': datetime.utcnow()
                }
            }
        )
    
    def _notify_admin_of_message(self, admin_id: ObjectId, message: ChatMessage):
        """Notify specific admin of new message."""
        admin_id_str = str(admin_id)
        if admin_id_str in self.admin_sessions:
            self.socketio.emit('new_message_for_admin', message.to_json_dict(),
                             room=self.admin_sessions[admin_id_str])

# Global instance will be initialized in main app
websocket_service = None

def init_websocket_service(socketio: SocketIO):
    """Initialize WebSocket service."""
    global websocket_service
    websocket_service = WebSocketChatService(socketio)
    return websocket_service