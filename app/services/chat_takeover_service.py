#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Chat Takeover Service
Handles silent admin takeover of customer conversations without revealing admin status.
Ensures seamless transition between AI and human responses.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bson import ObjectId

from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import ChatConversationV2 as ChatConversation, ChatMessageV2 as ChatMessage, MessageType, ConversationStatus
from app.services.ai_service_manager import ai_service
from app.utils.chat_utils import get_system_prompt

logger = logging.getLogger(__name__)

class ChatTakeoverService:
    """
    Service for managing silent admin takeover of customer conversations.
    Ensures customers never know when an admin has taken over from AI.
    """
    
    def __init__(self):
        self.active_takeovers = {}  # conversation_id -> admin_info
        self.takeover_queue = []    # Queue of conversations waiting for admin
        self.ai_response_delay = 2  # Seconds to wait before AI response
        self.admin_response_timeout = 300  # 5 minutes timeout for admin response
    
    def request_takeover(self, conversation_id: str, admin_id: str, admin_name: str) -> Dict:
        """
        Request admin takeover of a customer conversation.
        
        Args:
            conversation_id: ID of the conversation to take over
            admin_id: ID of the admin requesting takeover
            admin_name: Name of the admin
            
        Returns:
            Dict with success status and takeover info
        """
        try:
            # Check if conversation exists
            conversation = mongo_db.db.chat_conversations.find_one(
                {'conversation_id': conversation_id}
            )
            
            if not conversation:
                return {
                    'success': False,
                    'error': 'Conversation not found'
                }
            
            # Check if already taken over
            if conversation_id in self.active_takeovers:
                current_admin = self.active_takeovers[conversation_id]
                return {
                    'success': False,
                    'error': f'Conversation already taken over by {current_admin["admin_name"]}'
                }
            
            # Create admin session
            admin_session = AdminSession({
                'admin_id': admin_id,
                'admin_name': admin_name,
                'conversation_id': conversation_id,
                'takeover_time': datetime.utcnow(),
                'is_active': True,
                'last_activity': datetime.utcnow()
            })
            
            # Save admin session
            session_result = mongo_db.db.admin_sessions.insert_one(admin_session.to_dict())
            session_id = str(session_result.inserted_id)
            
            # Update conversation to mark admin takeover
            mongo_db.db.chat_conversations.update_one(
                {'conversation_id': conversation_id},
                {
                    '$set': {
                        'admin_taken_over': True,
                        'admin_id': admin_id,
                        'admin_name': admin_name,
                        'takeover_time': datetime.utcnow(),
                        'admin_session_id': session_id
                    }
                }
            )
            
            # Add to active takeovers
            self.active_takeovers[conversation_id] = {
                'admin_id': admin_id,
                'admin_name': admin_name,
                'session_id': session_id,
                'takeover_time': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
            
            logger.info(f"Admin {admin_name} took over conversation {conversation_id}")
            
            return {
                'success': True,
                'takeover_info': {
                    'conversation_id': conversation_id,
                    'admin_id': admin_id,
                    'admin_name': admin_name,
                    'session_id': session_id,
                    'takeover_time': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error requesting takeover: {e}")
            return {
                'success': False,
                'error': f'Failed to take over conversation: {str(e)}'
            }
    
    def release_takeover(self, conversation_id: str, admin_id: str) -> Dict:
        """
        Release admin takeover and return conversation to AI.
        
        Args:
            conversation_id: ID of the conversation to release
            admin_id: ID of the admin releasing takeover
            
        Returns:
            Dict with success status
        """
        try:
            # Check if conversation is taken over by this admin
            if conversation_id not in self.active_takeovers:
                return {
                    'success': False,
                    'error': 'Conversation is not taken over'
                }
            
            takeover_info = self.active_takeovers[conversation_id]
            if takeover_info['admin_id'] != admin_id:
                return {
                    'success': False,
                    'error': 'You are not the admin who took over this conversation'
                }
            
            # Update conversation to remove admin takeover
            mongo_db.db.chat_conversations.update_one(
                {'conversation_id': conversation_id},
                {
                    '$set': {
                        'admin_taken_over': False,
                        'release_time': datetime.utcnow()
                    },
                    '$unset': {
                        'admin_id': '',
                        'admin_name': '',
                        'admin_session_id': ''
                    }
                }
            )
            
            # Update admin session to inactive
            mongo_db.db.admin_sessions.update_one(
                {'_id': ObjectId(takeover_info['session_id'])},
                {
                    '$set': {
                        'is_active': False,
                        'release_time': datetime.utcnow()
                    }
                }
            )
            
            # Remove from active takeovers
            del self.active_takeovers[conversation_id]
            
            logger.info(f"Admin {takeover_info['admin_name']} released conversation {conversation_id}")
            
            return {
                'success': True,
                'message': 'Conversation released back to AI'
            }
            
        except Exception as e:
            logger.error(f"Error releasing takeover: {e}")
            return {
                'success': False,
                'error': f'Failed to release conversation: {str(e)}'
            }
    
    def is_conversation_taken_over(self, conversation_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a conversation is currently taken over by an admin.
        
        Args:
            conversation_id: ID of the conversation to check
            
        Returns:
            Tuple of (is_taken_over, admin_info)
        """
        if conversation_id in self.active_takeovers:
            return True, self.active_takeovers[conversation_id]
        
        # Also check database in case service was restarted
        conversation = mongo_db.db.chat_conversations.find_one(
            {
                'conversation_id': conversation_id,
                'admin_taken_over': True
            }
        )
        
        if conversation:
            # Restore to active takeovers
            admin_info = {
                'admin_id': conversation.get('admin_id'),
                'admin_name': conversation.get('admin_name'),
                'session_id': conversation.get('admin_session_id'),
                'takeover_time': conversation.get('takeover_time'),
                'last_activity': datetime.utcnow()
            }
            self.active_takeovers[conversation_id] = admin_info
            return True, admin_info
        
        return False, None
    
    def handle_customer_message(self, conversation_id: str, message: str, session_id: str) -> Dict:
        """
        Handle customer message - route to admin if taken over, otherwise to AI.
        
        Args:
            conversation_id: ID of the conversation
            message: Customer message
            session_id: Customer session ID
            
        Returns:
            Dict with routing information
        """
        try:
            is_taken_over, admin_info = self.is_conversation_taken_over(conversation_id)
            
            if is_taken_over:
                # Update admin activity
                self.active_takeovers[conversation_id]['last_activity'] = datetime.utcnow()
                
                return {
                    'route_to': 'admin',
                    'admin_info': admin_info,
                    'requires_admin_response': True
                }
            else:
                return {
                    'route_to': 'ai',
                    'requires_ai_response': True
                }
                
        except Exception as e:
            logger.error(f"Error handling customer message: {e}")
            # Default to AI on error
            return {
                'route_to': 'ai',
                'requires_ai_response': True,
                'error': str(e)
            }
    
    def send_admin_message(self, conversation_id: str, admin_id: str, message: str, 
                          appears_as_ai: bool = True) -> Dict:
        """
        Send message from admin that appears as AI to customer.
        
        Args:
            conversation_id: ID of the conversation
            admin_id: ID of the admin sending message
            message: Message content
            appears_as_ai: Whether message should appear as AI to customer
            
        Returns:
            Dict with success status and message info
        """
        try:
            # Verify admin has taken over this conversation
            is_taken_over, admin_info = self.is_conversation_taken_over(conversation_id)
            
            if not is_taken_over or admin_info['admin_id'] != admin_id:
                return {
                    'success': False,
                    'error': 'You have not taken over this conversation'
                }
            
            # Create admin message
            admin_message = ChatMessage({
                'conversation_id': conversation_id,
                'message_type': 'admin',
                'content': message,
                'sender_id': admin_id,
                'sender_name': admin_info['admin_name'],
                'appears_as_ai': appears_as_ai,
                'timestamp': datetime.utcnow(),
                'admin_session_id': admin_info['session_id']
            })
            
            # Save message
            message_result = mongo_db.db.chat_messages.insert_one(admin_message.to_dict())
            message_id = str(message_result.inserted_id)
            
            # Update admin activity
            self.active_takeovers[conversation_id]['last_activity'] = datetime.utcnow()
            
            logger.info(f"Admin {admin_info['admin_name']} sent message in conversation {conversation_id}")
            
            return {
                'success': True,
                'message_info': {
                    'message_id': message_id,
                    'conversation_id': conversation_id,
                    'content': message,
                    'appears_as_ai': appears_as_ai,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error sending admin message: {e}")
            return {
                'success': False,
                'error': f'Failed to send message: {str(e)}'
            }
    
    def get_active_takeovers(self, admin_id: Optional[str] = None) -> List[Dict]:
        """
        Get list of active takeovers, optionally filtered by admin.
        
        Args:
            admin_id: Optional admin ID to filter by
            
        Returns:
            List of active takeover information
        """
        try:
            takeovers = []
            
            for conversation_id, admin_info in self.active_takeovers.items():
                if admin_id and admin_info['admin_id'] != admin_id:
                    continue
                
                # Get conversation details
                conversation = mongo_db.db.chat_conversations.find_one(
                    {'conversation_id': conversation_id}
                )
                
                if conversation:
                    takeovers.append({
                        'conversation_id': conversation_id,
                        'admin_id': admin_info['admin_id'],
                        'admin_name': admin_info['admin_name'],
                        'takeover_time': admin_info['takeover_time'].isoformat(),
                        'last_activity': admin_info['last_activity'].isoformat(),
                        'customer_session_id': conversation.get('session_id'),
                        'customer_user_id': conversation.get('user_id'),
                        'language': conversation.get('language', 'english')
                    })
            
            return takeovers
            
        except Exception as e:
            logger.error(f"Error getting active takeovers: {e}")
            return []
    
    def cleanup_inactive_takeovers(self) -> int:
        """
        Clean up takeovers that have been inactive for too long.
        
        Returns:
            Number of takeovers cleaned up
        """
        try:
            cleanup_count = 0
            current_time = datetime.utcnow()
            timeout_threshold = current_time - timedelta(seconds=self.admin_response_timeout)
            
            # Find inactive takeovers
            inactive_conversations = []
            for conversation_id, admin_info in self.active_takeovers.items():
                if admin_info['last_activity'] < timeout_threshold:
                    inactive_conversations.append(conversation_id)
            
            # Release inactive takeovers
            for conversation_id in inactive_conversations:
                admin_info = self.active_takeovers[conversation_id]
                result = self.release_takeover(conversation_id, admin_info['admin_id'])
                if result['success']:
                    cleanup_count += 1
                    logger.info(f"Auto-released inactive takeover for conversation {conversation_id}")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive takeovers: {e}")
            return 0
    
    def get_conversation_context(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation context for admin takeover.
        
        Args:
            conversation_id: ID of the conversation
            limit: Number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        try:
            messages_cursor = mongo_db.db.chat_messages.find(
                {'conversation_id': conversation_id}
            ).sort('timestamp', -1).limit(limit)
            
            messages = []
            for msg_doc in messages_cursor:
                message = ChatMessage(msg_doc)
                messages.append({
                    'content': message.content,
                    'message_type': message.message_type,
                    'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                    'sender_name': getattr(message, 'sender_name', None),
                    'appears_as_ai': getattr(message, 'appears_as_ai', False)
                })
            
            # Reverse to get chronological order
            messages.reverse()
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []
    
    def generate_ai_response_with_context(self, conversation_id: str, message: str, 
                                        language: str = 'english') -> Dict:
        """
        Generate AI response with conversation context.
        
        Args:
            conversation_id: ID of the conversation
            message: Customer message
            language: Detected language
            
        Returns:
            Dict with AI response info
        """
        try:
            # Get conversation context
            context_messages = self.get_conversation_context(conversation_id, limit=5)
            
            # Prepare context for AI
            context = {
                'conversation_history': context_messages,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow()
            }
            
            # Get AI response
            ai_response = ai_service.get_ai_response(
                message=message,
                language=language,
                system_prompt=get_system_prompt(language),
                context=context
            )
            
            return {
                'success': True,
                'response': ai_response.content,
                'response_time_ms': ai_response.response_time_ms,
                'source': ai_response.source,
                'confidence': ai_response.confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_response': "I'm here to help! Could you please rephrase your question?"
            }

# Global instance
chat_takeover_service = ChatTakeoverService()