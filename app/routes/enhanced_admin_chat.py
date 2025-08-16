#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced Admin Chat Interface
Admin interface for managing enhanced chat system with role-based access.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import (
    ChatConversationV2, ChatMessageV2, AILearningData,
    MessageType, MessageVisibility, ConversationStatus, UserRole
)
from app.services.enhanced_ai_service import get_enhanced_ai_service
from app.utils.decorators import admin_required, super_admin_required

# Create blueprint
enhanced_admin_chat_bp = Blueprint('enhanced_admin_chat', __name__, url_prefix='/admin/chat/v2')

@enhanced_admin_chat_bp.route('/')
@login_required
@admin_required
def admin_chat_dashboard():
    """
    Enhanced admin chat dashboard.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get dashboard statistics
        stats = _get_dashboard_stats()
        
        # Get recent conversations
        recent_conversations = _get_recent_conversations(limit=10)
        
        # Get admin activity summary
        admin_activity = _get_admin_activity_summary()
        
        # Get AI learning insights
        ai_insights = _get_ai_learning_insights()
        
        return render_template(
            'admin/enhanced_chat_dashboard.html',
            stats=stats,
            recent_conversations=recent_conversations,
            admin_activity=admin_activity,
            ai_insights=ai_insights,
            admin_role=admin_role,
            user_roles=UserRole,
            message_types=MessageType,
            conversation_statuses=ConversationStatus,
            message_visibility=MessageVisibility
        )
        
    except Exception as e:
        return render_template(
            'admin/enhanced_chat_dashboard.html',
            error=f'Failed to load dashboard: {str(e)}',
            stats={},
            recent_conversations=[],
            admin_activity={},
            ai_insights={}
        )

@enhanced_admin_chat_bp.route('/conversations')
@login_required
@admin_required
def admin_conversations_list():
    """
    Enhanced admin conversations list with filtering.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get filter parameters
        status_filter = request.args.get('status', 'active')
        admin_filter = request.args.get('admin', '')
        language_filter = request.args.get('language', '')
        priority_filter = request.args.get('priority', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        search_query = request.args.get('search', '')
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get filtered conversations
        conversations_data = _get_filtered_conversations(
            admin_role=admin_role,
            status_filter=status_filter,
            admin_filter=admin_filter,
            language_filter=language_filter,
            priority_filter=priority_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
            page=page,
            per_page=per_page
        )
        
        # Get filter options
        filter_options = _get_filter_options(admin_role)
        
        return render_template(
            'admin/enhanced_conversations_list.html',
            conversations=conversations_data['conversations'],
            total_count=conversations_data['total_count'],
            page=page,
            per_page=per_page,
            total_pages=conversations_data['total_pages'],
            filter_options=filter_options,
            current_filters={
                'status': status_filter,
                'admin': admin_filter,
                'language': language_filter,
                'priority': priority_filter,
                'date_from': date_from,
                'date_to': date_to,
                'search': search_query
            },
            admin_role=admin_role
        )
        
    except Exception as e:
        return render_template(
            'admin/enhanced_conversations_list.html',
            error=f'Failed to load conversations: {str(e)}',
            conversations=[],
            total_count=0,
            page=1,
            per_page=20,
            total_pages=0,
            filter_options={},
            current_filters={}
        )

@enhanced_admin_chat_bp.route('/conversation/<conversation_id>')
@login_required
@admin_required
def admin_conversation_detail(conversation_id: str):
    """
    Enhanced admin conversation detail view.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get conversation
        conv_data = mongo_db.db.chat_conversations_v2.find_one({
            'conversation_id': conversation_id
        })
        
        if not conv_data:
            return render_template(
                'admin/enhanced_conversation_detail.html',
                error='Conversation not found',
                conversation=None
            )
        
        conversation = ChatConversationV2(conv_data)
        
        # Get all messages (filtered by admin role)
        messages = _get_messages_for_admin_view(
            conversation_id, 
            admin_role,
            include_internal=True
        )
        
        # Get admin notes
        admin_notes = conversation.admin_notes or []
        
        # Get AI learning data for this conversation
        learning_data = _get_conversation_learning_data(conversation_id)
        
        # Get conversation analytics
        conversation_analytics = _get_conversation_analytics(conversation_id)
        
        # Get available admins for assignment
        available_admins = _get_available_admins(admin_role)
        
        return render_template(
            'admin/enhanced_conversation_detail.html',
            conversation=conversation,
            messages=messages,
            admin_notes=admin_notes,
            learning_data=learning_data,
            conversation_analytics=conversation_analytics,
            available_admins=available_admins,
            admin_role=admin_role,
            current_admin_id=str(current_user.get_id()),
            message_types=MessageType,
            message_visibility=MessageVisibility,
            conversation_statuses=ConversationStatus
        )
        
    except Exception as e:
        return render_template(
            'admin/enhanced_conversation_detail.html',
            error=f'Failed to load conversation: {str(e)}',
            conversation=None
        )

@enhanced_admin_chat_bp.route('/ai-learning')
@login_required
@admin_required
def ai_learning_dashboard():
    """
    AI learning dashboard for admins.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get learning statistics
        learning_stats = _get_learning_statistics()
        
        # Get recent corrections
        recent_corrections = _get_recent_corrections(limit=20)
        
        # Get learning insights
        learning_insights = _get_detailed_learning_insights()
        
        # Get improvement suggestions
        improvement_suggestions = _get_improvement_suggestions()
        
        return render_template(
            'admin/ai_learning_dashboard.html',
            learning_stats=learning_stats,
            recent_corrections=recent_corrections,
            learning_insights=learning_insights,
            improvement_suggestions=improvement_suggestions,
            admin_role=admin_role
        )
        
    except Exception as e:
        return render_template(
            'admin/ai_learning_dashboard.html',
            error=f'Failed to load AI learning dashboard: {str(e)}',
            learning_stats={},
            recent_corrections=[],
            learning_insights={},
            improvement_suggestions=[]
        )

@enhanced_admin_chat_bp.route('/analytics')
@login_required
@admin_required
def chat_analytics():
    """
    Enhanced chat analytics dashboard.
    """
    try:
        admin_role = _get_user_role(current_user)
        
        # Get time range
        days = request.args.get('days', 7, type=int)
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Get comprehensive analytics
        analytics = _get_comprehensive_analytics(
            days=days,
            date_from=date_from,
            date_to=date_to,
            admin_role=admin_role
        )
        
        return render_template(
            'admin/enhanced_chat_analytics.html',
            analytics=analytics,
            days=days,
            date_from=date_from,
            date_to=date_to,
            admin_role=admin_role
        )
        
    except Exception as e:
        return render_template(
            'admin/enhanced_chat_analytics.html',
            error=f'Failed to load analytics: {str(e)}',
            analytics={},
            days=7,
            admin_role=admin_role
        )

@enhanced_admin_chat_bp.route('/settings')
@login_required
@super_admin_required
def chat_settings():
    """
    Enhanced chat system settings (Super Admin only).
    """
    try:
        # Get current settings
        settings = _get_chat_settings()
        
        # Get AI service status
        ai_service = get_enhanced_ai_service()
        ai_status = ai_service.get_service_status() if ai_service else {'status': 'unavailable'}
        
        # Get system health metrics
        health_metrics = _get_system_health_metrics()
        
        return render_template(
            'admin/enhanced_chat_settings.html',
            settings=settings,
            ai_status=ai_status,
            health_metrics=health_metrics
        )
        
    except Exception as e:
        return render_template(
            'admin/enhanced_chat_settings.html',
            error=f'Failed to load settings: {str(e)}',
            settings={},
            ai_status={},
            health_metrics={}
        )

# API endpoints for AJAX operations
@enhanced_admin_chat_bp.route('/api/conversation/<conversation_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_conversation(conversation_id: str):
    """
    Assign conversation to admin.
    """
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        
        if not admin_id:
            return jsonify({
                'success': False,
                'error': 'Admin ID required'
            }), 400
        
        # Update conversation assignment
        result = mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {
                '$set': {
                    'assigned_admin_id': ObjectId(admin_id),
                    'assigned_at': datetime.utcnow(),
                    'assigned_by': ObjectId(current_user.get_id())
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Conversation assigned successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to assign conversation: {str(e)}'
        }), 500

@enhanced_admin_chat_bp.route('/api/conversation/<conversation_id>/escalate', methods=['POST'])
@login_required
@admin_required
def escalate_conversation(conversation_id: str):
    """
    Escalate conversation to higher level.
    """
    try:
        data = request.get_json()
        escalation_reason = data.get('reason', '')
        escalation_level = data.get('level', 1)
        
        # Update conversation
        result = mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {
                '$set': {
                    'status': ConversationStatus.ESCALATED.value,
                    'escalation_level': escalation_level,
                    'escalation_reason': escalation_reason,
                    'escalated_at': datetime.utcnow(),
                    'escalated_by': ObjectId(current_user.get_id())
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        # Create escalation log message
        escalation_message = ChatMessageV2({
            'conversation_id': ObjectId(conversation_id),
            'message_type': MessageType.SYSTEM.value,
            'content': f"Conversation escalated by {current_user.full_name}. Reason: {escalation_reason}",
            'timestamp': datetime.utcnow(),
            'visibility': MessageVisibility.ADMIN_ONLY.value,
            'is_internal': True,
            'escalation_flag': True,
            'escalation_level': escalation_level,
            'sender_id': ObjectId(current_user.get_id()),
            'sender_name': current_user.full_name,
            'sender_role': _get_user_role(current_user)
        })
        
        mongo_db.db.chat_messages_v2.insert_one(escalation_message.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Conversation escalated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to escalate conversation: {str(e)}'
        }), 500

@enhanced_admin_chat_bp.route('/api/conversation/<conversation_id>/priority', methods=['POST'])
@login_required
@admin_required
def update_conversation_priority(conversation_id: str):
    """
    Update conversation priority.
    """
    try:
        data = request.get_json()
        priority_level = data.get('priority', 'normal')
        
        if priority_level not in ['low', 'normal', 'high', 'urgent']:
            return jsonify({
                'success': False,
                'error': 'Invalid priority level'
            }), 400
        
        # Update conversation priority
        result = mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {
                '$set': {
                    'priority_level': priority_level,
                    'priority_updated_at': datetime.utcnow(),
                    'priority_updated_by': ObjectId(current_user.get_id())
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Priority updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update priority: {str(e)}'
        }), 500

@enhanced_admin_chat_bp.route('/api/conversation/<conversation_id>/note', methods=['POST'])
@login_required
@admin_required
def add_admin_note(conversation_id: str):
    """
    Add admin note to conversation.
    """
    try:
        data = request.get_json()
        note_content = data.get('note', '').strip()
        note_type = data.get('type', 'general')
        
        if not note_content:
            return jsonify({
                'success': False,
                'error': 'Note content required'
            }), 400
        
        # Create admin note
        admin_note = {
            'id': str(ObjectId()),
            'content': note_content,
            'type': note_type,
            'created_at': datetime.utcnow(),
            'created_by': ObjectId(current_user.get_id()),
            'admin_name': current_user.full_name
        }
        
        # Add note to conversation
        result = mongo_db.db.chat_conversations_v2.update_one(
            {'conversation_id': conversation_id},
            {'$push': {'admin_notes': admin_note}}
        )
        
        if result.modified_count == 0:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'note': {
                'id': admin_note['id'],
                'content': admin_note['content'],
                'type': admin_note['type'],
                'created_at': admin_note['created_at'].isoformat(),
                'admin_name': admin_note['admin_name']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to add note: {str(e)}'
        }), 500

@enhanced_admin_chat_bp.route('/api/learning/retrain', methods=['POST'])
@login_required
@super_admin_required
def retrain_ai_model():
    """
    Trigger AI model retraining (Super Admin only).
    """
    try:
        ai_service = get_enhanced_ai_service()
        if not ai_service:
            return jsonify({
                'success': False,
                'error': 'AI service not available'
            }), 503
        
        # Trigger retraining
        retrain_result = ai_service.trigger_model_retraining()
        
        return jsonify(retrain_result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to trigger retraining: {str(e)}'
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

def _get_dashboard_stats() -> Dict:
    """Get dashboard statistics."""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        stats = {
            'conversations': {
                'total_today': 0,
                'total_week': 0,
                'active_now': 0,
                'admin_taken': 0,
                'escalated': 0
            },
            'messages': {
                'total_today': 0,
                'total_week': 0,
                'ai_responses': 0,
                'admin_responses': 0,
                'internal_messages': 0
            },
            'ai_performance': {
                'avg_confidence': 0.0,
                'corrections_today': 0,
                'learning_entries': 0,
                'response_time_avg': 0.0
            },
            'admin_activity': {
                'active_admins': 0,
                'total_takeovers': 0,
                'avg_response_time': 0.0
            }
        }
        
        # Get conversation stats
        conv_stats = list(mongo_db.db.chat_conversations_v2.aggregate([
            {
                '$facet': {
                    'today': [
                        {'$match': {'created_at': {'$gte': today}}},
                        {'$count': 'count'}
                    ],
                    'week': [
                        {'$match': {'created_at': {'$gte': week_ago}}},
                        {'$count': 'count'}
                    ],
                    'by_status': [
                        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
                    ]
                }
            }
        ]))
        
        if conv_stats:
            conv_data = conv_stats[0]
            stats['conversations']['total_today'] = conv_data['today'][0]['count'] if conv_data['today'] else 0
            stats['conversations']['total_week'] = conv_data['week'][0]['count'] if conv_data['week'] else 0
            
            for status_stat in conv_data['by_status']:
                status = status_stat['_id']
                count = status_stat['count']
                if status == ConversationStatus.ACTIVE.value:
                    stats['conversations']['active_now'] = count
                elif status == ConversationStatus.ADMIN_TAKEN.value:
                    stats['conversations']['admin_taken'] = count
                elif status == ConversationStatus.ESCALATED.value:
                    stats['conversations']['escalated'] = count
        
        # Get message stats
        msg_stats = list(mongo_db.db.chat_messages_v2.aggregate([
            {
                '$facet': {
                    'today': [
                        {'$match': {'timestamp': {'$gte': today}}},
                        {'$count': 'count'}
                    ],
                    'week': [
                        {'$match': {'timestamp': {'$gte': week_ago}}},
                        {'$count': 'count'}
                    ],
                    'by_type': [
                        {'$group': {
                            '_id': '$message_type',
                            'count': {'$sum': 1},
                            'avg_confidence': {'$avg': '$ai_confidence'}
                        }}
                    ]
                }
            }
        ]))
        
        if msg_stats:
            msg_data = msg_stats[0]
            stats['messages']['total_today'] = msg_data['today'][0]['count'] if msg_data['today'] else 0
            stats['messages']['total_week'] = msg_data['week'][0]['count'] if msg_data['week'] else 0
            
            for type_stat in msg_data['by_type']:
                msg_type = type_stat['_id']
                count = type_stat['count']
                if msg_type == MessageType.AI.value:
                    stats['messages']['ai_responses'] = count
                    stats['ai_performance']['avg_confidence'] = type_stat.get('avg_confidence', 0.0) or 0.0
                elif msg_type == MessageType.ADMIN.value:
                    stats['messages']['admin_responses'] = count
                elif msg_type == MessageType.INTERNAL.value:
                    stats['messages']['internal_messages'] = count
        
        # Get AI learning stats
        learning_count = mongo_db.db.ai_learning_data.count_documents({
            'created_at': {'$gte': week_ago}
        })
        stats['ai_performance']['learning_entries'] = learning_count
        
        corrections_today = mongo_db.db.ai_learning_data.count_documents({
            'created_at': {'$gte': today}
        })
        stats['ai_performance']['corrections_today'] = corrections_today
        
        return stats
        
    except Exception as e:
        return {}

def _get_recent_conversations(limit: int = 10) -> List[Dict]:
    """Get recent conversations for dashboard."""
    try:
        conversations_cursor = mongo_db.db.chat_conversations_v2.find().sort(
            'last_activity', -1
        ).limit(limit)
        
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
                'last_activity': conversation.last_activity,
                'total_messages': conversation.total_messages,
                'priority_level': conversation.priority_level,
                'language_detected': conversation.language_detected
            }
            
            if last_message:
                conv_info['last_message'] = {
                    'content': last_message['content'][:50] + '...' if len(last_message['content']) > 50 else last_message['content'],
                    'timestamp': last_message['timestamp'],
                    'message_type': last_message['message_type']
                }
            
            conversations.append(conv_info)
        
        return conversations
        
    except Exception as e:
        return []

def _get_admin_activity_summary() -> Dict:
    """Get admin activity summary."""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        activity = list(mongo_db.db.chat_messages_v2.aggregate([
            {
                '$match': {
                    'timestamp': {'$gte': today},
                    'is_admin_message': True
                }
            },
            {
                '$group': {
                    '_id': '$sender_name',
                    'message_count': {'$sum': 1},
                    'corrections': {
                        '$sum': {'$cond': [{'$eq': ['$admin_override', True]}, 1, 0]}
                    },
                    'last_activity': {'$max': '$timestamp'}
                }
            }
        ]))
        
        return {admin['_id']: {
            'messages': admin['message_count'],
            'corrections': admin['corrections'],
            'last_activity': admin['last_activity']
        } for admin in activity}
        
    except Exception as e:
        return {}

def _get_ai_learning_insights() -> Dict:
    """Get AI learning insights."""
    try:
        ai_service = get_enhanced_ai_service()
        if ai_service:
            return ai_service.get_learning_statistics(days=7)
        return {}
        
    except Exception as e:
        return {}

def _get_filtered_conversations(admin_role: str, **filters) -> Dict:
    """Get filtered conversations with pagination."""
    try:
        query = {}
        
        # Apply filters
        if filters.get('status_filter') and filters['status_filter'] != 'all':
            if filters['status_filter'] == 'active':
                query['status'] = {'$in': [ConversationStatus.ACTIVE.value, ConversationStatus.ADMIN_TAKEN.value]}
            else:
                query['status'] = filters['status_filter']
        
        if filters.get('language_filter'):
            query['language_detected'] = filters['language_filter']
        
        if filters.get('priority_filter'):
            query['priority_level'] = filters['priority_filter']
        
        if filters.get('admin_filter'):
            query['admin_taken_by'] = ObjectId(filters['admin_filter'])
        
        # Date range filter
        if filters.get('date_from') or filters.get('date_to'):
            date_query = {}
            if filters.get('date_from'):
                date_query['$gte'] = datetime.fromisoformat(filters['date_from'])
            if filters.get('date_to'):
                date_query['$lte'] = datetime.fromisoformat(filters['date_to'])
            query['created_at'] = date_query
        
        # Search query
        if filters.get('search_query'):
            query['$text'] = {'$search': filters['search_query']}
        
        # Get total count
        total_count = mongo_db.db.chat_conversations_v2.count_documents(query)
        
        # Calculate pagination
        page = filters.get('page', 1)
        per_page = filters.get('per_page', 20)
        skip = (page - 1) * per_page
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get conversations
        conversations_cursor = mongo_db.db.chat_conversations_v2.find(query).sort(
            'last_activity', -1
        ).skip(skip).limit(per_page)
        
        conversations = []
        for conv_data in conversations_cursor:
            conversation = ChatConversationV2(conv_data)
            conversations.append(conversation.to_dict())
        
        return {
            'conversations': conversations,
            'total_count': total_count,
            'total_pages': total_pages
        }
        
    except Exception as e:
        return {
            'conversations': [],
            'total_count': 0,
            'total_pages': 0
        }

def _get_filter_options(admin_role: str) -> Dict:
    """Get available filter options."""
    try:
        options = {
            'statuses': [status.value for status in ConversationStatus],
            'languages': [],
            'priorities': ['low', 'normal', 'high', 'urgent'],
            'admins': []
        }
        
        # Get available languages
        languages = mongo_db.db.chat_conversations_v2.distinct('language_detected')
        options['languages'] = [lang for lang in languages if lang]
        
        # Get available admins (if super admin)
        if admin_role == UserRole.SUPER_ADMIN.value:
            # This would need to be implemented based on your user model
            pass
        
        return options
        
    except Exception as e:
        return {}

def _get_messages_for_admin_view(conversation_id: str, admin_role: str, include_internal: bool = True) -> List[Dict]:
    """Get messages for admin view."""
    try:
        query = {'conversation_id': ObjectId(conversation_id)}
        
        # Filter based on admin role
        if admin_role == UserRole.ADMIN.value and include_internal:
            # Regular admins can't see super admin only messages
            query['visibility'] = {'$ne': MessageVisibility.SUPER_ADMIN_ONLY.value}
        
        messages_cursor = mongo_db.db.chat_messages_v2.find(query).sort('timestamp', 1)
        
        messages = []
        for msg_doc in messages_cursor:
            message = ChatMessageV2(msg_doc)
            formatted_message = {
                'id': str(message._id),
                'content': message.content,
                'timestamp': message.timestamp,
                'message_type': message.message_type,
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
            }
            messages.append(formatted_message)
        
        return messages
        
    except Exception as e:
        return []

def _get_conversation_learning_data(conversation_id: str) -> List[Dict]:
    """Get AI learning data for conversation."""
    try:
        learning_cursor = mongo_db.db.ai_learning_data.find({
        'conversation_id': conversation_id
    }).sort('created_at', -1)
        
        learning_data = []
        for ld in learning_cursor:
            learning_data.append({
                'id': str(ld['_id']),
                'original_message': ld['original_message'],
                'ai_response': ld['ai_response'],
                'admin_correction': ld['admin_correction'],
                'correction_reason': ld['correction_reason'],
                'improvement_category': ld['improvement_category'],
                'admin_name': ld['admin_name'],
                'created_at': ld['created_at']
            })
        
        return learning_data
        
    except Exception as e:
        return []

def _get_conversation_analytics(conversation_id: str) -> Dict:
    """Get analytics for specific conversation."""
    try:
        analytics = {
            'message_count_by_type': {},
            'response_times': [],
            'ai_confidence_trend': [],
            'admin_interventions': 0,
            'escalations': 0
        }
        
        # Get message type distribution
        type_stats = list(mongo_db.db.chat_messages_v2.aggregate([
            {'$match': {'conversation_id': conversation_id}},
            {'$group': {'_id': '$message_type', 'count': {'$sum': 1}}}
        ]))
        
        for stat in type_stats:
            analytics['message_count_by_type'][stat['_id']] = stat['count']
        
        # Count admin interventions
        admin_interventions = mongo_db.db.chat_messages_v2.count_documents({
            'conversation_id': conversation_id,
            'is_admin_message': True
        })
        analytics['admin_interventions'] = admin_interventions
        
        # Count escalations
        escalations = mongo_db.db.chat_messages_v2.count_documents({
            'conversation_id': conversation_id,
            'escalation_flag': True
        })
        analytics['escalations'] = escalations
        
        return analytics
        
    except Exception as e:
        return {}

def _get_available_admins(admin_role: str) -> List[Dict]:
    """Get list of available admins."""
    # This would need to be implemented based on your user model
    # For now, return empty list
    return []

def _get_learning_statistics() -> Dict:
    """Get comprehensive learning statistics."""
    try:
        ai_service = get_enhanced_ai_service()
        if ai_service:
            return ai_service.get_learning_statistics(days=30)
        return {}
        
    except Exception as e:
        return {}

def _get_recent_corrections(limit: int = 20) -> List[Dict]:
    """Get recent AI corrections."""
    try:
        corrections_cursor = mongo_db.db.ai_learning_data.find().sort(
            'created_at', -1
        ).limit(limit)
        
        corrections = []
        for correction in corrections_cursor:
            corrections.append({
                'id': str(correction['_id']),
                'original_message': correction['original_message'],
                'ai_response': correction['ai_response'][:100] + '...' if len(correction['ai_response']) > 100 else correction['ai_response'],
                'admin_correction': correction['admin_correction'][:100] + '...' if len(correction['admin_correction']) > 100 else correction['admin_correction'],
                'correction_reason': correction['correction_reason'],
                'improvement_category': correction['improvement_category'],
                'admin_name': correction['admin_name'],
                'created_at': correction['created_at']
            })
        
        return corrections
        
    except Exception as e:
        return []

def _get_detailed_learning_insights() -> Dict:
    """Get detailed learning insights."""
    try:
        insights = {
            'top_correction_categories': [],
            'language_performance': {},
            'confidence_trends': [],
            'improvement_suggestions': []
        }
        
        # Get top correction categories
        category_stats = list(mongo_db.db.ai_learning_data.aggregate([
            {'$group': {
                '_id': '$improvement_category',
                'count': {'$sum': 1},
                'avg_confidence_before': {'$avg': '$confidence_before'},
                'avg_confidence_improvement': {'$avg': '$confidence_improvement'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))
        
        insights['top_correction_categories'] = category_stats
        
        return insights
        
    except Exception as e:
        return {}

def _get_improvement_suggestions() -> List[Dict]:
    """Get AI improvement suggestions."""
    try:
        ai_service = get_enhanced_ai_service()
        if ai_service:
            return ai_service.get_improvement_suggestions()
        return []
        
    except Exception as e:
        return []

def _get_comprehensive_analytics(days: int, date_from: str, date_to: str, admin_role: str) -> Dict:
    """Get comprehensive analytics."""
    try:
        # This would implement detailed analytics
        # For now, return basic structure
        return {
            'conversations': {},
            'messages': {},
            'ai_performance': {},
            'admin_activity': {},
            'trends': {},
            'insights': {}
        }
        
    except Exception as e:
        return {}

def _get_chat_settings() -> Dict:
    """Get current chat system settings."""
    try:
        # This would get settings from database or config
        return {
            'ai_enabled': True,
            'auto_takeover_threshold': 3,
            'escalation_timeout': 300,
            'max_conversation_length': 100,
            'learning_enabled': True,
            'confidence_threshold': 0.7
        }
        
    except Exception as e:
        return {}

def _get_system_health_metrics() -> Dict:
    """Get system health metrics."""
    try:
        return {
            'database_status': 'healthy',
            'ai_service_status': 'healthy',
            'websocket_connections': 0,
            'active_conversations': 0,
            'memory_usage': '45%',
            'response_time_avg': 250
        }
        
    except Exception as e:
        return {}