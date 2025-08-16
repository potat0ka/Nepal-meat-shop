#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced Chat Routes
API routes for enhanced chat system with role-based access and AI learning.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import (
    ChatConversationV2, ChatMessageV2, AILearningData,
    MessageType, MessageVisibility, ConversationStatus, UserRole
)
from app.services.enhanced_ai_service import get_enhanced_ai_service
from app.utils.chat_utils import detect_language, validate_session_id
from app.routes.mongo_admin import admin_required, staff_required

# Create blueprint
enhanced_chat_bp = Blueprint('enhanced_chat', __name__, url_prefix='/api/v2/chat')

@enhanced_chat_bp.route('/start', methods=['POST'])
def start_conversation():
    """
    Start a new chat conversation.
    """
    try:
        data = request.get_json() or {}
        
        # Generate session ID if not provided
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Validate session ID format
        if not validate_session_id(session_id):
            return jsonify({
                'success': False,
                'error': 'Invalid session ID format'
            }), 400
        
        # Check if conversation already exists
        existing_conv = mongo_db.db.chat_conversations_v2.find_one({
            'session_id': session_id
        })
        
        if existing_conv:
            conversation = ChatConversationV2(existing_conv)
            return jsonify({
                'success': True,
                'conversation_id': conversation.conversation_id,
                'session_id': session_id,
                'status': conversation.status,
                'message': 'Existing conversation resumed'
            })
        
        # Create new conversation
        conversation = ChatConversationV2({
            'conversation_id': str(uuid.uuid4()),
            'session_id': session_id,
            'customer_ip': request.remote_addr,
            'customer_user_agent': request.headers.get('User-Agent', ''),
            'status': ConversationStatus.ACTIVE.value,
            'language_detected': data.get('language', 'en'),
            'customer_metadata': {
                'referrer': request.headers.get('Referer', ''),
                'initial_page': data.get('initial_page', ''),
                'device_type': data.get('device_type', 'unknown')
            }
        })
        
        # Save to database
        result = mongo_db.db.chat_conversations_v2.insert_one(conversation.to_dict())
        conversation._id = result.inserted_id
        
        # Send welcome message
        welcome_message = _get_welcome_message(conversation.language_detected)
        
        welcome_msg = ChatMessageV2({
            'conversation_id': conversation.conversation_id,
            'session_id': session_id,
            'message_type': MessageType.AI.value,
            'content': welcome_message,
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.PUBLIC.value,
            'ai_response_source': 'welcome',
            'language_detected': conversation.language_detected
        })
        
        # Save welcome message
        mongo_db.db.chat_messages_v2.insert_one(welcome_msg.to_dict())
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.conversation_id,
            'session_id': session_id,
            'status': conversation.status,
            'welcome_message': welcome_message,
            'message': 'New conversation started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start conversation: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/history/<session_id>', methods=['GET'])
def get_conversation_history(session_id: str):
    """
    Get conversation history for a session.
    """
    try:
        # Validate session ID
        if not validate_session_id(session_id):
            return jsonify({
                'success': False,
                'error': 'Invalid session ID format'
            }), 400
        
        # Get conversation
        conv_data = mongo_db.db.chat_conversations_v2.find_one({
            'session_id': session_id
        })
        
        if not conv_data:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        conversation = ChatConversationV2(conv_data)
        
        # Determine user role for filtering
        user_role = UserRole.CUSTOMER.value
        if current_user.is_authenticated:
            user_role = _get_user_role(current_user)
        
        # Get messages filtered by role
        messages = _get_messages_for_role(
            conversation.conversation_id, 
            user_role,
            limit=request.args.get('limit', 50, type=int),
            offset=request.args.get('offset', 0, type=int)
        )
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.conversation_id,
            'session_id': session_id,
            'status': conversation.status,
            'messages': messages,
            'total_messages': conversation.total_messages,
            'is_admin_active': conversation.is_admin_active
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get conversation history: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/send', methods=['POST'])
def send_message():
    """
    Send a message in a conversation.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        session_id = data.get('session_id')
        message_content = data.get('message', '').strip()
        
        if not session_id or not message_content:
            return jsonify({
                'success': False,
                'error': 'Session ID and message are required'
            }), 400
        
        # Get conversation
        conv_data = mongo_db.db.chat_conversations_v2.find_one({
            'session_id': session_id
        })
        
        if not conv_data:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        conversation = ChatConversationV2(conv_data)
        
        # Detect language
        detected_language = detect_language(message_content)
        
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
            'language_detected': detected_language
        })
        
        # Save customer message
        result = mongo_db.db.chat_messages_v2.insert_one(customer_message.to_dict())
        customer_message._id = result.inserted_id
        
        # Update conversation activity and message count
        mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation.conversation_id},
            {
                '$set': {'last_activity': datetime.utcnow()},
                '$inc': {'total_messages': 1}
            }
        )
        
        # Generate AI response if admin is not active
        ai_response = None
        if not conversation.is_admin_active:
            ai_response = _generate_ai_response(conversation, customer_message)
        
        response_data = {
            'success': True,
            'message_id': str(customer_message._id),
            'conversation_id': conversation.conversation_id,
            'timestamp': customer_message.timestamp.isoformat(),
            'is_admin_active': conversation.is_admin_active
        }
        
        if ai_response:
            response_data['ai_response'] = {
                'message_id': str(ai_response._id),
                'content': ai_response.content,
                'timestamp': ai_response.timestamp.isoformat()
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to send message: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/conversations', methods=['GET'])
@login_required
@admin_required
def get_admin_conversations():
    """
    Get conversations for admin dashboard.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get query parameters
        status_filter = request.args.get('status', 'active')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = {}
        if status_filter == 'active':
            query['status'] = {'$in': [ConversationStatus.ACTIVE.value, ConversationStatus.ADMIN_TAKEN.value]}
        elif status_filter == 'escalated':
            query['status'] = ConversationStatus.ESCALATED.value
        elif status_filter != 'all':
            query['status'] = status_filter
        
        # Add time filter for active conversations
        if status_filter == 'active':
            since = datetime.utcnow() - timedelta(hours=24)
            query['last_activity'] = {'$gte': since}
        
        # Get conversations
        conversations_cursor = mongo_db.db.chat_conversations_v2.find(query).sort(
            'last_activity', -1
        ).skip(offset).limit(limit)
        
        conversations = []
        for conv_data in conversations_cursor:
            conversation = ChatConversationV2(conv_data)
            
            # Get last message
            last_message = mongo_db.db.chat_messages_v2.find_one(
                {'conversation_id': ObjectId(conversation.conversation_id)},
                sort=[('timestamp', -1)]
            )
            
            conv_info = {
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
                'escalation_level': conversation.escalation_level,
                'language_detected': conversation.language_detected
            }
            
            if last_message:
                conv_info['last_message'] = {
                    'content': last_message['content'][:100] + '...' if len(last_message['content']) > 100 else last_message['content'],
                    'timestamp': last_message['timestamp'].isoformat(),
                    'message_type': last_message['message_type']
                }
            
            conversations.append(conv_info)
        
        # Get total count
        total_count = mongo_db.db.chat_conversations_v2.count_documents(query)
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get admin conversations: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/conversation/<conversation_id>', methods=['GET'])
@login_required
@admin_required
def get_admin_conversation_details(conversation_id: str):
    """
    Get detailed conversation information for admin.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get conversation
        conv_data = mongo_db.db.chat_conversations_v2.find_one({
            'conversation_id': conversation_id
        })
        
        if not conv_data:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        conversation = ChatConversationV2(conv_data)
        
        # Get all messages (admin can see all)
        messages = _get_messages_for_role(
            conversation_id, 
            admin_role,
            include_internal=True
        )
        
        # Get admin notes
        admin_notes = conversation.admin_notes or []
        
        # Get learning data for this conversation
        learning_data = list(mongo_db.db.ai_learning_data.find({
            'conversation_id': conversation_id
        }).sort('created_at', -1))
        
        return jsonify({
            'success': True,
            'conversation': {
                'conversation_id': conversation.conversation_id,
                'session_id': conversation.session_id,
                'status': conversation.status,
                'is_admin_active': conversation.is_admin_active,
                'admin_taken_by': str(conversation.admin_taken_by) if conversation.admin_taken_by else None,
                'admin_taken_at': conversation.admin_taken_at.isoformat() if conversation.admin_taken_at else None,
                'created_at': conversation.created_at.isoformat(),
                'last_activity': conversation.last_activity.isoformat(),
                'total_messages': conversation.total_messages,
                'total_internal_messages': conversation.total_internal_messages,
                'admin_corrections_count': conversation.admin_corrections_count,
                'priority_level': conversation.priority_level,
                'escalation_level': conversation.escalation_level,
                'language_detected': conversation.language_detected,
                'customer_ip': conversation.customer_ip,
                'customer_user_agent': conversation.customer_user_agent,
                'customer_metadata': conversation.customer_metadata
            },
            'messages': messages,
            'admin_notes': admin_notes,
            'learning_data': [{
                'id': str(ld['_id']),
                'original_message': ld['original_message'],
                'ai_response': ld['ai_response'],
                'admin_correction': ld['admin_correction'],
                'correction_reason': ld['correction_reason'],
                'improvement_category': ld['improvement_category'],
                'admin_name': ld['admin_name'],
                'created_at': ld['created_at'].isoformat()
            } for ld in learning_data]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get conversation details: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/takeover', methods=['POST'])
@login_required
@admin_required
def admin_takeover():
    """
    Admin takeover of a conversation.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({
                'success': False,
                'error': 'Conversation ID required'
            }), 400
        
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
            return jsonify({
                'success': False,
                'error': 'Conversation already taken or not found'
            }), 409
        
        # Create takeover log message
        takeover_message = ChatMessageV2({
            'conversation_id': conversation_id,
            'message_type': MessageType.SYSTEM.value,
            'content': f"Admin {current_user.full_name} has taken over this conversation",
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.ADMIN_ONLY.value,
            'is_internal': True,
            'sender_id': ObjectId(current_user.get_id()),
            'sender_name': current_user.full_name,
            'sender_role': _get_user_role(current_user)
        })
        
        mongo_db.db.chat_messages_v2.insert_one(takeover_message.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Conversation taken over successfully',
            'admin_name': current_user.full_name
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to take over conversation: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/release', methods=['POST'])
@login_required
@admin_required
def admin_release():
    """
    Admin release of a conversation.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({
                'success': False,
                'error': 'Conversation ID required'
            }), 400
        
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
            return jsonify({
                'success': False,
                'error': 'Conversation not found or not taken by you'
            }), 404
        
        # Create release log message
        release_message = ChatMessageV2({
            'conversation_id': conversation_id,
            'message_type': MessageType.SYSTEM.value,
            'content': f"Admin {current_user.full_name} has released this conversation",
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.ADMIN_ONLY.value,
            'is_internal': True,
            'sender_id': ObjectId(current_user.get_id()),
            'sender_name': current_user.full_name,
            'sender_role': _get_user_role(current_user)
        })
        
        mongo_db.db.chat_messages_v2.insert_one(release_message.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Conversation released successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to release conversation: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/send', methods=['POST'])
@login_required
@admin_required
def admin_send_message():
    """
    Admin send message to customer.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conversation_id = data.get('conversation_id')
        message_content = data.get('message', '').strip()
        appears_as_ai = data.get('appears_as_ai', True)
        
        if not conversation_id or not message_content:
            return jsonify({
                'success': False,
                'error': 'Conversation ID and message are required'
            }), 400
        
        # Get conversation
        conv_data = mongo_db.db.chat_conversations_v2.find_one({
            'conversation_id': conversation_id
        })
        
        if not conv_data:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        conversation = ChatConversationV2(conv_data)
        
        # Create admin message
        admin_message = ChatMessageV2({
            'conversation_id': ObjectId(conversation_id),
            'session_id': conversation.session_id,
            'message_type': MessageType.AI.value if appears_as_ai else MessageType.ADMIN.value,
            'content': message_content,
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.PUBLIC.value,
            'sender_id': ObjectId(current_user.get_id()),
            'sender_name': current_user.full_name,
            'sender_role': _get_user_role(current_user),
            'is_admin_message': True,
            'admin_id': ObjectId(current_user.get_id()),
            'appears_as_ai': appears_as_ai,
            'language_detected': detect_language(message_content)
        })
        
        # Save message
        result = mongo_db.db.chat_messages_v2.insert_one(admin_message.to_dict())
        admin_message._id = result.inserted_id
        
        # Update conversation activity
        mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {
                '$set': {'last_activity': datetime.utcnow()},
                '$inc': {'total_messages': 1}
            }
        )
        
        return jsonify({
            'success': True,
            'message_id': str(admin_message._id),
            'timestamp': admin_message.timestamp.isoformat(),
            'appears_as_ai': appears_as_ai
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to send admin message: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/internal', methods=['POST'])
@login_required
@admin_required
def admin_send_internal_message():
    """
    Admin send internal message (not visible to customer).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conversation_id = data.get('conversation_id')
        message_content = data.get('message', '').strip()
        internal_tags = data.get('tags', [])
        visibility = data.get('visibility', MessageVisibility.ADMIN_ONLY.value)
        
        if not conversation_id or not message_content:
            return jsonify({
                'success': False,
                'error': 'Conversation ID and message are required'
            }), 400
        
        admin_role = _get_user_role(current_user)
        
        # Validate visibility based on admin role
        if visibility == MessageVisibility.SUPER_ADMIN_ONLY.value and admin_role != UserRole.SUPER_ADMIN.value:
            return jsonify({
                'success': False,
                'error': 'Super admin access required for this visibility level'
            }), 403
        
        # Create internal message
        internal_message = ChatMessageV2({
            'conversation_id': ObjectId(conversation_id),
            'message_type': MessageType.INTERNAL.value,
            'content': message_content,
            'timestamp': datetime.utcnow(),
            'visibility': visibility,
            'is_internal': True,
            'sender_id': ObjectId(current_user.get_id()),
            'sender_name': current_user.full_name,
            'sender_role': admin_role,
            'internal_tags': internal_tags,
            'visible_to_roles': _get_visible_roles_for_visibility(visibility)
        })
        
        # Save message
        result = mongo_db.db.chat_messages_v2.insert_one(internal_message.to_dict())
        internal_message._id = result.inserted_id
        
        # Update conversation internal message count
        mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {'$inc': {'total_internal_messages': 1}}
        )
        
        return jsonify({
            'success': True,
            'message_id': str(internal_message._id),
            'timestamp': internal_message.timestamp.isoformat(),
            'visibility': visibility
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to send internal message: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/correct', methods=['POST'])
@login_required
@admin_required
def admin_correct_ai_response():
    """
    Admin correct AI response for learning.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conversation_id = data.get('conversation_id')
        original_message_id = data.get('original_message_id')
        corrected_response = data.get('corrected_response', '').strip()
        correction_reason = data.get('correction_reason', '')
        improvement_category = data.get('improvement_category', '')
        
        if not all([conversation_id, original_message_id, corrected_response]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields for correction'
            }), 400
        
        # Get original AI message
        try:
            original_message = mongo_db.db.chat_messages_v2.find_one({
                '_id': ObjectId(original_message_id),
                'conversation_id': conversation_id,
                'message_type': MessageType.AI.value
            })
        except InvalidId:
            return jsonify({
                'success': False,
                'error': 'Invalid message ID format'
            }), 400
        
        if not original_message:
            return jsonify({
                'success': False,
                'error': 'Original AI message not found'
            }), 404
        
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
            'confidence_before': original_message.get('ai_confidence', 0.0),
            'confidence_improvement': 0.2  # Default improvement
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
        
        return jsonify({
            'success': True,
            'message': 'AI response corrected successfully',
            'learning_data_id': str(learning_data._id) if hasattr(learning_data, '_id') else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to correct AI response: {str(e)}'
        }), 500

@enhanced_chat_bp.route('/admin/analytics', methods=['GET'])
@login_required
@admin_required
def get_chat_analytics():
    """
    Get chat analytics for admin dashboard.
    """
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get AI service for learning statistics
        ai_service = get_enhanced_ai_service()
        
        analytics = {
            'period_days': days,
            'conversations': {
                'total': 0,
                'active': 0,
                'admin_taken': 0,
                'escalated': 0
            },
            'messages': {
                'total': 0,
                'ai_messages': 0,
                'admin_messages': 0,
                'internal_messages': 0
            },
            'ai_performance': {
                'total_corrections': 0,
                'avg_confidence': 0.0,
                'learning_entries': 0
            },
            'languages': {},
            'response_times': [],
            'admin_activity': {}
        }
        
        # Get conversation statistics
        conv_stats = list(mongo_db.db.chat_conversations_v2.aggregate([
            {'$match': {'created_at': {'$gte': since}}},
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }}
        ]))
        
        for stat in conv_stats:
            status = stat['_id']
            count = stat['count']
            analytics['conversations']['total'] += count
            
            if status == ConversationStatus.ACTIVE.value:
                analytics['conversations']['active'] = count
            elif status == ConversationStatus.ADMIN_TAKEN.value:
                analytics['conversations']['admin_taken'] = count
            elif status == ConversationStatus.ESCALATED.value:
                analytics['conversations']['escalated'] = count
        
        # Get message statistics
        msg_stats = list(mongo_db.db.chat_messages_v2.aggregate([
            {'$match': {'timestamp': {'$gte': since}}},
            {'$group': {
                '_id': '$message_type',
                'count': {'$sum': 1},
                'avg_confidence': {'$avg': '$ai_confidence'}
            }}
        ]))
        
        for stat in msg_stats:
            msg_type = stat['_id']
            count = stat['count']
            analytics['messages']['total'] += count
            
            if msg_type == MessageType.AI.value:
                analytics['messages']['ai_messages'] = count
                analytics['ai_performance']['avg_confidence'] = stat.get('avg_confidence', 0.0) or 0.0
            elif msg_type == MessageType.ADMIN.value:
                analytics['messages']['admin_messages'] = count
            elif msg_type == MessageType.INTERNAL.value:
                analytics['messages']['internal_messages'] = count
        
        # Get AI learning statistics
        if ai_service:
            learning_stats = ai_service.get_learning_statistics(days)
            if 'error' not in learning_stats:
                analytics['ai_performance'].update({
                    'total_corrections': learning_stats.get('total_corrections', 0),
                    'learning_entries': learning_stats.get('total_learning_entries', 0),
                    'languages': learning_stats.get('languages', {}),
                    'improvement_categories': learning_stats.get('improvement_categories', {})
                })
        
        # Get language distribution
        lang_stats = list(mongo_db.db.chat_conversations_v2.aggregate([
            {'$match': {'created_at': {'$gte': since}}},
            {'$group': {
                '_id': '$language_detected',
                'count': {'$sum': 1}
            }}
        ]))
        
        for stat in lang_stats:
            lang = stat['_id'] or 'unknown'
            analytics['languages'][lang] = stat['count']
        
        # Get admin activity
        admin_stats = list(mongo_db.db.chat_messages_v2.aggregate([
            {
                '$match': {
                    'timestamp': {'$gte': since},
                    'is_admin_message': True
                }
            },
            {
                '$group': {
                    '_id': '$sender_name',
                    'message_count': {'$sum': 1},
                    'corrections_made': {
                        '$sum': {'$cond': [{'$eq': ['$admin_override', True]}, 1, 0]}
                    }
                }
            }
        ]))
        
        for stat in admin_stats:
            admin_name = stat['_id'] or 'Unknown'
            analytics['admin_activity'][admin_name] = {
                'messages': stat['message_count'],
                'corrections': stat['corrections_made']
            }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get analytics: {str(e)}'
        }), 500

# Helper functions
def _get_user_role(user) -> str:
    """Get user role from user object."""
    if hasattr(user, 'role'):
        if user.role == 'super_admin':
            return UserRole.SUPER_ADMIN.value
        elif user.role in ['admin', 'sub_admin']:
            return UserRole.ADMIN.value
    return UserRole.USER.value

def _get_visible_roles_for_visibility(visibility: str) -> List[str]:
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

def _get_messages_for_role(conversation_id: str, user_role: str, limit: int = 50, offset: int = 0, include_internal: bool = False) -> List[Dict]:
    """Get messages filtered by user role."""
    try:
        # Build query based on role
        query = {'conversation_id': conversation_id}
        
        if user_role == UserRole.CUSTOMER.value:
            # Customers only see public messages
            query['visibility'] = MessageVisibility.PUBLIC.value
            query['is_internal'] = {'$ne': True}
        elif user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            # Admins can see more based on their role
            if not include_internal:
                query['is_internal'] = {'$ne': True}
            elif user_role == UserRole.ADMIN.value:
                # Regular admins can't see super admin only messages
                query['visibility'] = {'$ne': MessageVisibility.SUPER_ADMIN_ONLY.value}
        
        messages_cursor = mongo_db.db.chat_messages_v2.find(query).sort(
            'timestamp', 1
        ).skip(offset).limit(limit)
        
        messages = []
        for msg_doc in messages_cursor:
            message = ChatMessageV2(msg_doc)
            formatted_message = _format_message_for_role(message, user_role)
            if formatted_message:
                messages.append(formatted_message)
        
        return messages
        
    except Exception as e:
        return []

def _format_message_for_role(message: ChatMessageV2, user_role: str) -> Optional[Dict]:
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
            'escalation_flag': message.escalation_flag,
            'edited': message.edited,
            'admin_correction': message.admin_correction
        })
    
    return formatted

def _get_welcome_message(language: str) -> str:
    """Get welcome message in specified language."""
    welcome_messages = {
        'en': "Hello! Welcome to Nepal Meat Shop. I'm here to help you with our fresh meat products and services. How can I assist you today?",
        'ne': "नमस्कार! नेपाल मीट शपमा स्वागत छ। म यहाँ तपाईंलाई हाम्रो ताजा मासुका उत्पादन र सेवाहरूमा मद्दत गर्न छु। आज म तपाईंलाई कसरी सहायता गर्न सक्छु?"
    }
    return welcome_messages.get(language, welcome_messages['en'])

def _generate_ai_response(conversation: ChatConversationV2, customer_message: ChatMessageV2) -> Optional[ChatMessageV2]:
    """Generate AI response to customer message."""
    try:
        ai_service = get_enhanced_ai_service()
        if not ai_service:
            return None
        
        # Get conversation context
        context_messages = _get_conversation_context(conversation.conversation_id, limit=5)
        
        # Get AI response
        ai_response = ai_service.get_ai_response(
            message=customer_message.content,
            language=customer_message.language_detected or 'en',
            context={'conversation_history': context_messages}
        )
        
        if ai_response.get('success'):
            # Create AI message
            ai_message = ChatMessageV2({
                'conversation_id': ObjectId(conversation.conversation_id),
                'session_id': conversation.session_id,
                'message_type': MessageType.AI.value,
                'content': ai_response['response'],
                'timestamp': datetime.utcnow(),
                'visibility': MessageVisibility.PUBLIC.value,
                'ai_response_source': ai_response.get('source', 'ai'),
                'ai_confidence': ai_response.get('confidence', 0.0),
                'ai_response_time_ms': ai_response.get('response_time_ms', 0),
                'ai_model_used': ai_response.get('model_used', 'gpt-4o-mini'),
                'language_detected': customer_message.language_detected
            })
            
            # Save AI message
            result = mongo_db.db.chat_messages_v2.insert_one(ai_message.to_dict())
            ai_message._id = result.inserted_id
            
            # Update conversation message count
            mongo_db.db.chat_conversations_v2.update_one(
                {'conversation_id': conversation.conversation_id},
                {'$inc': {'total_messages': 1}}
            )
            
            return ai_message
        
        return None
        
    except Exception as e:
        return None

def _get_conversation_context(conversation_id: str, limit: int = 10) -> List[Dict]:
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
        return []