#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Chat Routes
AI Chat Assistant routes with enhanced reliability, caching, and fallback mechanisms.
Featuring Ebregel - Your intelligent meat shop assistant.
"""

import os
import time
import re
import threading
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import current_user

from bson.objectid import ObjectId
from app.utils.mongo_db import mongo_db
from app.models.chat import MongoChat
from app.models.enhanced_chat import ChatConversation, ChatMessage
from app.services.ai_service_manager import ai_service
from app.utils.chat_utils import get_system_prompt, detect_language

# Create chat blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api')

# Removed - now using ai_service_manager

# Performance monitoring and optimization
performance_metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'avg_response_time': 0.0,
    'cache_hit_rate': 0.0,
    'last_reset': datetime.utcnow(),
    'response_times': [],
    'error_types': {},
    'peak_usage_hours': {},
    'user_satisfaction_avg': 0.0
}
metrics_lock = threading.Lock()

def _update_performance_metrics(response_time, success=True, error_type=None, cached=False):
    """Update performance metrics with thread safety"""
    with metrics_lock:
        performance_metrics['total_requests'] += 1
        
        if success:
            performance_metrics['successful_requests'] += 1
        else:
            performance_metrics['failed_requests'] += 1
            if error_type:
                performance_metrics['error_types'][error_type] = performance_metrics['error_types'].get(error_type, 0) + 1
        
        # Update response times (keep last 1000 for rolling average)
        performance_metrics['response_times'].append(response_time)
        if len(performance_metrics['response_times']) > 1000:
            performance_metrics['response_times'] = performance_metrics['response_times'][-1000:]
        
        # Calculate rolling average
        if performance_metrics['response_times']:
            performance_metrics['avg_response_time'] = sum(performance_metrics['response_times']) / len(performance_metrics['response_times'])
        
        # Track peak usage by hour
        current_hour = datetime.utcnow().hour
        performance_metrics['peak_usage_hours'][current_hour] = performance_metrics['peak_usage_hours'].get(current_hour, 0) + 1

def _get_performance_insights():
    """Generate performance insights and recommendations"""
    insights = []
    
    with metrics_lock:
        # Response time analysis
        if performance_metrics['avg_response_time'] > 3000:  # 3 seconds
            insights.append("High response times detected. Consider optimizing AI service or increasing cache usage.")
        
        # Error rate analysis
        if performance_metrics['total_requests'] > 0:
            error_rate = performance_metrics['failed_requests'] / performance_metrics['total_requests']
            if error_rate > 0.1:  # 10% error rate
                insights.append(f"High error rate ({error_rate:.1%}). Check AI service stability.")
        
        # Cache efficiency
        cache_stats = ai_service.get_stats()
        if cache_stats.get('cache_hit_rate', 0) < 0.3:  # Less than 30% cache hit rate
            insights.append("Low cache hit rate. Consider expanding cache duration or improving cache keys.")
        
        # Peak usage recommendations
        if performance_metrics['peak_usage_hours']:
            peak_hour = max(performance_metrics['peak_usage_hours'], key=performance_metrics['peak_usage_hours'].get)
            insights.append(f"Peak usage at hour {peak_hour}. Consider scaling resources during this time.")
    
    return insights

def _update_learning_data(user_message, bot_reply, language, source):
    """Update learning data for self-improvement."""
    try:
        learning_collection = mongo_db.db.chat_learning
        learning_data = {
            'user_message': user_message,
            'bot_reply': bot_reply,
            'language': language,
            'source': source,
            'timestamp': datetime.utcnow(),
            'message_length': len(user_message),
            'reply_length': len(bot_reply),
            'keywords': _extract_keywords(user_message),
            'intent': _classify_intent(user_message),
            'satisfaction_score': None  # To be updated by user feedback
        }
        learning_collection.insert_one(learning_data)
    except Exception as e:
        current_app.logger.error(f"Failed to save learning data: {e}")

def _extract_keywords(text):
    """Extract keywords from user message for learning."""
    # Simple keyword extraction - can be enhanced with NLP libraries
    keywords = []
    text_lower = text.lower()
    
    # Product keywords
    product_keywords = ['chicken', 'mutton', 'fish', 'meat', 'kukhura', 'khasi', 'machha', 'masu']
    for keyword in product_keywords:
        if keyword in text_lower:
            keywords.append(keyword)
    
    # Action keywords
    action_keywords = ['order', 'buy', 'price', 'delivery', 'cost', 'available']
    for keyword in action_keywords:
        if keyword in text_lower:
            keywords.append(keyword)
    
    return keywords

def _classify_intent(text):
    """Classify user intent for learning purposes."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['price', 'cost', 'rate', 'paisa', 'rupiya', 'kati']):
        return 'price_inquiry'
    elif any(word in text_lower for word in ['delivery', 'deliver', 'order', 'pathau']):
        return 'delivery_inquiry'
    elif any(word in text_lower for word in ['available', 'stock', 'have', 'chha']):
        return 'availability_inquiry'
    elif any(word in text_lower for word in ['hello', 'hi', 'namaste', 'hey']):
        return 'greeting'
    elif any(word in text_lower for word in ['help', 'support', 'problem', 'issue']):
        return 'support_request'
    else:
        return 'general_inquiry'

# Language detection and system prompt functions moved to app.utils.chat_utils

def get_enhanced_chat_history(session_id, conversation_id=None):
    """Get chat history from enhanced chat system."""
    try:
        # Find conversation by session_id or conversation_id
        query = {}
        if conversation_id:
            query['conversation_id'] = conversation_id
        elif session_id:
            query['session_id'] = session_id
        else:
            return jsonify({'success': False, 'error': 'Session ID required'}), 400
        
        # Get conversation
        conversation = mongo_db.db.chat_conversations.find_one(query)
        if not conversation:
            return jsonify({'success': True, 'history': []}), 200
        
        # Get messages for this conversation
        messages_cursor = mongo_db.db.chat_messages.find(
            {'conversation_id': conversation['conversation_id']}
        ).sort('timestamp', 1)  # Ascending order for history
        
        # Format messages for frontend
        history = []
        for msg_doc in messages_cursor:
            message = ChatMessage(msg_doc)
            history.append({
                'content': message.content,
                'message_type': message.message_type,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'appears_as_ai': getattr(message, 'appears_as_ai', False)
            })
        
        return jsonify({
            'success': True,
            'history': history,
            'conversation_id': conversation['conversation_id']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting enhanced chat history: {e}")
        return jsonify({'success': False, 'error': 'Failed to load chat history'}), 500

# System prompt function moved to app.utils.chat_utils

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with Ebregel AI assistant - Enhanced with reliability features and WebSocket integration."""
    try:
        # Get request data
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get session ID for enhanced chat tracking
        session_id = data.get('session_id')
        conversation_id = data.get('conversation_id')
        
        # Detect language
        detected_language = detect_language(user_message)
        
        # Prepare system prompt
        system_prompt = get_system_prompt(detected_language)
        
        # Prepare context for better responses
        context = {
            'user_authenticated': current_user.is_authenticated,
            'user_id': current_user.get_id() if current_user.is_authenticated else None,
            'timestamp': datetime.utcnow(),
            'session_info': request.headers.get('User-Agent', '')
        }
        
        # Get AI response using the enhanced service manager
        ai_response = ai_service.get_ai_response(
            message=user_message,
            language=detected_language,
            system_prompt=system_prompt,
            context=context
        )
        
        # Update performance metrics
        _update_performance_metrics(
            response_time=ai_response.response_time_ms,
            success=True,
            cached=ai_response.cached
        )
        
        # Create enhanced chat record with additional metadata
        chat_data = {
            'user_message': user_message,
            'bot_reply': ai_response.content,
            'timestamp': ai_response.timestamp,
            'language_detected': detected_language,
            'response_time_ms': ai_response.response_time_ms,
            'response_source': ai_response.source,  # 'ai', 'cache', or 'fallback'
            'confidence_score': ai_response.confidence,
            'cached_response': ai_response.cached
        }
        
        # Add user ID if logged in
        if current_user.is_authenticated:
            chat_data['user_id'] = current_user.get_id()
        
        # Save to MongoDB with enhanced error handling
        try:
            chat_record = MongoChat(chat_data)
            mongo_db.db.chats.insert_one(chat_record.to_dict())
            
            # Update learning data for self-improvement
            _update_learning_data(user_message, ai_response.content, detected_language, ai_response.source)
            
        except Exception as e:
            current_app.logger.error(f"Failed to save chat to database: {e}")
            # Continue anyway - don't fail the request if DB save fails
        
        # Prepare response data
        response_data = {
            'reply': ai_response.content,
            'language_detected': detected_language,
            'response_time_ms': ai_response.response_time_ms,
            'source': ai_response.source,
            'confidence': ai_response.confidence,
            'assistant_name': 'Ebregel'
        }
        
        # If session_id is provided, handle enhanced chat integration
        if session_id:
            try:
                # Create or get conversation for enhanced chat
                conversation = None
                if conversation_id:
                    # Try to get existing conversation
                    conversation_doc = mongo_db.db.chat_conversations.find_one({'_id': ObjectId(conversation_id)})
                    if conversation_doc:
                        conversation = ChatConversation(conversation_doc)
                
                if not conversation:
                    # Create new conversation
                    conversation_data = {
                        'session_id': session_id,
                        'user_id': ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
                        'status': 'active',
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow(),
                        'is_admin_active': False,
                        'admin_taken_by': None,
                        'admin_taken_at': None
                    }
                    conversation = ChatConversation(conversation_data)
                    conversation_id = mongo_db.db.chat_conversations.insert_one(conversation.to_dict()).inserted_id
                    conversation._id = conversation_id
                
                # Save customer message
                customer_message = ChatMessage({
                    'conversation_id': conversation._id,
                    'session_id': session_id,
                    'message_type': 'customer',
                    'content': user_message,
                    'sender_id': ObjectId(current_user.get_id()) if current_user.is_authenticated else None,
                    'timestamp': datetime.utcnow()
                })
                mongo_db.db.chat_messages.insert_one(customer_message.to_dict())
                
                # Save AI response
                ai_message = ChatMessage({
                    'conversation_id': conversation._id,
                    'session_id': session_id,
                    'message_type': 'ai',
                    'content': ai_response.content,
                    'timestamp': datetime.utcnow(),
                    'response_time_ms': ai_response.response_time_ms,
                    'confidence_score': ai_response.confidence
                })
                mongo_db.db.chat_messages.insert_one(ai_message.to_dict())
                
                # Update conversation activity
                mongo_db.db.chat_conversations.update_one(
                    {'_id': conversation._id},
                    {'$set': {'updated_at': datetime.utcnow()}}
                )
                
                # Include conversation_id in response
                response_data['conversation_id'] = str(conversation._id)
                response_data['session_id'] = session_id
                
            except Exception as e:
                current_app.logger.error(f"Enhanced chat integration error: {e}")
                # Continue with regular response if enhanced chat fails
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Chat endpoint error: {e}")
        
        # Update performance metrics for failed request
        _update_performance_metrics(
            response_time=0,
            success=False,
            error_type=type(e).__name__
        )
        
        # Even in case of complete failure, provide a helpful fallback
        fallback_message = "I'm Ebregel, and I'm here to help! There seems to be a technical issue right now. Please try refreshing the page or contact us directly."
        return jsonify({
            'reply': fallback_message,
            'language_detected': 'english',
            'response_time_ms': 0,
            'source': 'emergency_fallback',
            'confidence': 0.5,
            'assistant_name': 'Ebregel'
        }), 200  # Return 200 instead of 500 to avoid breaking the UI

@chat_bp.route('/chat/history', methods=['GET'])
def chat_history():
    """Get chat history for current user - supports both old and enhanced chat systems."""
    try:
        # Get session ID for enhanced chat
        session_id = request.args.get('session_id')
        conversation_id = request.args.get('conversation_id')
        
        # If session_id is provided, use enhanced chat system
        if session_id:
            return get_enhanced_chat_history(session_id, conversation_id)
        
        # Fallback to old chat system for authenticated users
        if not current_user.is_authenticated:
            return jsonify({'success': True, 'history': []}), 200
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Query chat history for current user
        user_id = current_user.get_id()
        chats_cursor = mongo_db.db.chats.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).skip(skip).limit(per_page)
        
        # Convert to list and format for JSON
        chats = []
        for chat_doc in chats_cursor:
            chat = MongoChat(chat_doc)
            chats.append(chat.to_json_dict())
        
        # Get total count for pagination
        total_count = mongo_db.db.chats.count_documents({'user_id': user_id})
        
        return jsonify({
            'success': True,
            'history': chats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat history endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/chat/stats', methods=['GET'])
def chat_stats():
    """Get comprehensive chat and AI service statistics (admin only)."""
    try:
        if not current_user.is_authenticated or not current_user.has_admin_access():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get basic statistics
        total_chats = mongo_db.db.chats.count_documents({})
        
        # Language distribution
        language_pipeline = [
            {'$group': {
                '_id': '$language_detected',
                'count': {'$sum': 1}
            }}
        ]
        language_stats = list(mongo_db.db.chats.aggregate(language_pipeline))
        
        # Get chats by source (AI, cache, fallback)
        source_pipeline = [
            {'$group': {
                '_id': '$response_source',
                'count': {'$sum': 1}
            }}
        ]
        source_stats = list(mongo_db.db.chats.aggregate(source_pipeline))
        
        # Average response time and confidence
        avg_response_pipeline = [
            {'$group': {
                '_id': None,
                'avg_response_time': {'$avg': '$response_time_ms'},
                'avg_confidence': {'$avg': '$confidence_score'}
            }}
        ]
        avg_response_result = list(mongo_db.db.chats.aggregate(avg_response_pipeline))
        avg_response_time = avg_response_result[0]['avg_response_time'] if avg_response_result else 0
        avg_confidence = avg_response_result[0]['avg_confidence'] if avg_response_result else 0
        
        # Get AI service manager statistics
        ai_service_stats = ai_service.get_stats()
        
        # Get learning data statistics
        learning_stats = mongo_db.db.chat_learning.count_documents({})
        
        return jsonify({
            'total_chats': total_chats,
            'language_distribution': language_stats,
            'source_distribution': source_stats,
            'average_response_time_ms': round(avg_response_time, 2),
            'average_confidence': round(avg_confidence, 2),
            'ai_service_stats': ai_service_stats,
            'learning_entries': learning_stats,
            'assistant_name': 'Ebregel'
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat stats endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/chat/feedback', methods=['POST'])
def chat_feedback():
    """Collect user feedback on chat responses for learning."""
    try:
        data = request.get_json()
        if not data or 'chat_id' not in data or 'rating' not in data:
            return jsonify({'error': 'chat_id and rating are required'}), 400
        
        chat_id = data['chat_id']
        rating = data['rating']  # 1-5 scale
        feedback_text = data.get('feedback_text', '')
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
        
        # Update chat record with feedback
        update_result = mongo_db.db.chats.update_one(
            {'_id': chat_id},
            {
                '$set': {
                    'user_rating': rating,
                    'user_feedback': feedback_text,
                    'feedback_timestamp': datetime.utcnow()
                }
            }
        )
        
        if update_result.matched_count == 0:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Update learning data with satisfaction score
        mongo_db.db.chat_learning.update_many(
            {
                'timestamp': {'$gte': datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            },
            {
                '$set': {
                    'satisfaction_score': rating
                }
            }
        )
        
        return jsonify({
            'message': 'Feedback recorded successfully',
            'rating': rating
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat feedback endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/ai-service/stats', methods=['GET'])
def ai_service_stats():
    """Get detailed AI service statistics (admin only)."""
    try:
        if not current_user.is_authenticated or not current_user.has_admin_access():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get comprehensive AI service statistics
        stats = ai_service.get_detailed_stats()
        
        return jsonify({
            'ai_service_stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"AI service stats endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/ai-service/health', methods=['GET'])
def ai_service_health():
    """Check AI service health status."""
    try:
        health_status = ai_service.health_check()
        
        return jsonify({
            'status': 'healthy' if health_status['all_services_ok'] else 'degraded',
            'services': health_status['services'],
            'fallback_available': health_status['fallback_available'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"AI service health endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@chat_bp.route('/chat/learning-data', methods=['GET'])
def get_learning_data():
    """Get learning data for analysis (admin only)."""
    try:
        if not current_user.is_authenticated or not current_user.has_admin_access():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        
        # Get filters
        language_filter = request.args.get('language')
        intent_filter = request.args.get('intent')
        min_rating = request.args.get('min_rating', type=int)
        
        # Build query
        query = {}
        if language_filter:
            query['language'] = language_filter
        if intent_filter:
            query['intent'] = intent_filter
        if min_rating:
            query['satisfaction_score'] = {'$gte': min_rating}
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Query learning data
        learning_cursor = mongo_db.db.chat_learning.find(query).sort('timestamp', -1).skip(skip).limit(per_page)
        
        # Convert to list
        learning_data = []
        for doc in learning_cursor:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            learning_data.append(doc)
        
        # Get total count
        total_count = mongo_db.db.chat_learning.count_documents(query)
        
        return jsonify({
            'learning_data': learning_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'filters_applied': {
                'language': language_filter,
                'intent': intent_filter,
                'min_rating': min_rating
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Learning data endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/chat/performance', methods=['GET'])
def chat_performance():
    """Get performance metrics and insights (admin only)."""
    try:
        if not current_user.is_authenticated or not current_user.has_admin_access():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get performance insights
        insights = _get_performance_insights()
        
        # Get current metrics snapshot
        with metrics_lock:
            current_metrics = performance_metrics.copy()
        
        # Calculate additional metrics
        success_rate = 0
        if current_metrics['total_requests'] > 0:
            success_rate = current_metrics['successful_requests'] / current_metrics['total_requests']
        
        return jsonify({
            'performance_metrics': current_metrics,
            'success_rate': round(success_rate, 3),
            'insights': insights,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Performance metrics endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/chat-page')
def chat_page():
    """Serve the chat page frontend interface."""
    return render_template('chat/chat.html')