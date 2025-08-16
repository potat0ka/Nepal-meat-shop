from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models.enhanced_chat import ChatConversation, ChatMessage, AdminSession
from app.services.websocket_service import WebSocketChatService
from datetime import datetime, timedelta
import logging

# Create blueprint
admin_chat_bp = Blueprint('admin_chat', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

@admin_chat_bp.route('/chat-management')
@login_required
def chat_management():
    """
    Admin chat management interface
    """
    # Check if user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
        return render_template('errors/403.html'), 403
    
    return render_template('admin/chat_management.html')

@admin_chat_bp.route('/api/conversations')
@login_required
def get_conversations():
    """
    Get all active conversations for admin dashboard
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get conversations from last 24 hours that are still active
        since = datetime.utcnow() - timedelta(hours=24)
        
        conversations = ChatConversation.get_active_conversations(since=since)
        
        # Format conversations for frontend
        formatted_conversations = []
        for conv in conversations:
            # Get message count
            message_count = ChatMessage.count_messages(conv['_id'])
            
            # Get last message
            last_message = ChatMessage.get_last_message(conv['_id'])
            
            formatted_conv = {
                '_id': str(conv['_id']),
                'session_id': conv['session_id'],
                'customer_id': conv.get('customer_id'),
                'is_admin_active': conv.get('is_admin_active', False),
                'admin_taken_by': conv.get('admin_taken_by'),
                'created_at': conv['created_at'].isoformat(),
                'last_activity': conv['last_activity'].isoformat(),
                'language_detected': conv.get('language_detected', 'en'),
                'total_messages': message_count,
                'last_message': last_message['content'] if last_message else None,
                'status': 'admin_taken' if conv.get('is_admin_active') else 'ai_handling'
            }
            
            formatted_conversations.append(formatted_conv)
        
        # Sort by last activity (most recent first)
        formatted_conversations.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return jsonify({
            'success': True,
            'conversations': formatted_conversations,
            'total': len(formatted_conversations)
        })
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({'error': 'Failed to load conversations'}), 500

@admin_chat_bp.route('/api/conversation/<conversation_id>/messages')
@login_required
def get_conversation_messages(conversation_id):
    """
    Get messages for a specific conversation
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Get messages
        messages = ChatMessage.get_conversation_messages(
            conversation_id, 
            page=page, 
            limit=limit
        )
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                '_id': str(msg['_id']),
                'conversation_id': str(msg['conversation_id']),
                'message_type': msg['message_type'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_admin_message': msg.get('is_admin_message', False),
                'admin_id': msg.get('admin_id'),
                'appears_as_ai': msg.get('appears_as_ai', False),
                'sender_info': msg.get('sender_info', {})
            }
            formatted_messages.append(formatted_msg)
        
        return jsonify({
            'success': True,
            'messages': formatted_messages,
            'page': page,
            'has_more': len(formatted_messages) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        return jsonify({'error': 'Failed to load messages'}), 500

@admin_chat_bp.route('/api/conversation/<conversation_id>/takeover', methods=['POST'])
@login_required
def takeover_conversation(conversation_id):
    """
    Admin takes over a conversation from AI
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get conversation
        conversation = ChatConversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Check if already taken by another admin
        if conversation.get('is_admin_active') and conversation.get('admin_taken_by') != current_user.get_id():
            admin_session = AdminSession.get_by_admin_id(conversation['admin_taken_by'])
            admin_name = admin_session['admin_name'] if admin_session else 'Another admin'
            return jsonify({
                'error': f'Conversation is already being handled by {admin_name}'
            }), 409
        
        # Take over conversation
        success = ChatConversation.set_admin_takeover(
            conversation_id,
            admin_id=current_user.get_id(),
            admin_name=getattr(current_user, 'full_name', current_user.username)
        )
        
        if success:
            # Create/update admin session
            AdminSession.create_or_update(
                admin_id=current_user.get_id(),
                admin_name=getattr(current_user, 'full_name', current_user.username),
                socket_id=None  # Will be updated by WebSocket handler
            )
            
            # Log the takeover
            ChatMessage.create(
                conversation_id=conversation_id,
                message_type='system',
                content=f"Admin {getattr(current_user, 'full_name', current_user.username)} took over the conversation",
                is_admin_message=True,
                admin_id=current_user.get_id(),
                appears_as_ai=False
            )
            
            return jsonify({
                'success': True,
                'message': 'Conversation taken over successfully'
            })
        else:
            return jsonify({'error': 'Failed to take over conversation'}), 500
            
    except Exception as e:
        logger.error(f"Error taking over conversation: {str(e)}")
        return jsonify({'error': 'Failed to take over conversation'}), 500

@admin_chat_bp.route('/api/conversation/<conversation_id>/release', methods=['POST'])
@login_required
def release_conversation(conversation_id):
    """
    Admin releases conversation back to AI
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get conversation
        conversation = ChatConversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Check if admin owns this conversation
        if conversation.get('admin_taken_by') != current_user.get_id():
            return jsonify({'error': 'You can only release conversations you have taken over'}), 403
        
        # Release conversation
        success = ChatConversation.release_from_admin(conversation_id)
        
        if success:
            # Log the release
            ChatMessage.create(
                conversation_id=conversation_id,
                message_type='system',
                content=f"Admin {getattr(current_user, 'full_name', current_user.username)} released the conversation back to AI",
                is_admin_message=True,
                admin_id=current_user.get_id(),
                appears_as_ai=False
            )
            
            return jsonify({
                'success': True,
                'message': 'Conversation released to AI successfully'
            })
        else:
            return jsonify({'error': 'Failed to release conversation'}), 500
            
    except Exception as e:
        logger.error(f"Error releasing conversation: {str(e)}")
        return jsonify({'error': 'Failed to release conversation'}), 500

@admin_chat_bp.route('/api/conversation/<conversation_id>/send-message', methods=['POST'])
@login_required
def send_admin_message(conversation_id):
    """
    Admin sends a message in a conversation
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        appears_as_ai = data.get('appears_as_ai', True)
        
        # Get conversation
        conversation = ChatConversation.get_by_id(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Check if admin has taken over this conversation
        if not conversation.get('is_admin_active') or conversation.get('admin_taken_by') != current_user.get_id():
            return jsonify({'error': 'You must take over the conversation first'}), 403
        
        # Create message
        message = ChatMessage.create(
            conversation_id=conversation_id,
            message_type='admin' if not appears_as_ai else 'ai',
            content=message_content,
            is_admin_message=True,
            admin_id=current_user.get_id(),
            appears_as_ai=appears_as_ai,
            sender_info={
                'admin_name': getattr(current_user, 'full_name', current_user.username),
                'admin_role': getattr(current_user, 'role', 'admin')
            }
        )
        
        if message:
            # Update conversation last activity
            ChatConversation.update_last_activity(conversation_id)
            
            return jsonify({
                'success': True,
                'message': {
                    '_id': str(message['_id']),
                    'content': message['content'],
                    'message_type': message['message_type'],
                    'timestamp': message['timestamp'].isoformat(),
                    'appears_as_ai': appears_as_ai,
                    'is_admin_message': True
                }
            })
        else:
            return jsonify({'error': 'Failed to send message'}), 500
            
    except Exception as e:
        logger.error(f"Error sending admin message: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

@admin_chat_bp.route('/api/stats')
@login_required
def get_chat_stats():
    """
    Get chat statistics for admin dashboard
    """
    try:
        # Check admin privileges
        if not hasattr(current_user, 'role') or current_user.role not in ['admin', 'sub_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get stats for last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        
        stats = {
            'active_conversations': ChatConversation.count_active_conversations(since),
            'total_messages_today': ChatMessage.count_messages_since(since),
            'admin_taken_conversations': ChatConversation.count_admin_taken_conversations(),
            'ai_handled_conversations': ChatConversation.count_ai_handled_conversations(since),
            'online_admins': AdminSession.count_active_sessions()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {str(e)}")
        return jsonify({'error': 'Failed to load statistics'}), 500

# Error handlers
@admin_chat_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@admin_chat_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500