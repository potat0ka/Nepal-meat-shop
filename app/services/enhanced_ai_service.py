#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Enhanced AI Service
AI service with learning capabilities from admin corrections and context awareness.
"""

import json
import logging
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson.objectid import ObjectId

from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import MessageType, MessageVisibility, UserRole
from app.utils.chat_utils import detect_language, get_system_prompt

class EnhancedAIService:
    """
    Enhanced AI service with learning capabilities and context awareness.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(model)
        
        # Learning cache
        self.learning_cache = {}
        self.cache_refresh_interval = timedelta(hours=1)
        self.last_cache_refresh = datetime.utcnow()
        
        # Response templates for different scenarios
        self.response_templates = {
            'greeting': {
                'en': "Hello! Welcome to Nepal Meat Shop. How can I help you today?",
                'ne': "नमस्कार! नेपाल मीट शपमा स्वागत छ। आज म तपाईंलाई कसरी मद्दत गर्न सक्छु?"
            },
            'product_inquiry': {
                'en': "I'd be happy to help you with information about our meat products. What specific product are you interested in?",
                'ne': "म तपाईंलाई हाम्रो मासुका उत्पादनहरूको बारेमा जानकारी दिन खुसी छु। तपाईं कुन विशेष उत्पादनमा रुचि राख्नुहुन्छ?"
            },
            'order_help': {
                'en': "I can help you with placing an order. Let me guide you through our available products and ordering process.",
                'ne': "म तपाईंलाई अर्डर गर्न मद्दत गर्न सक्छु। मलाई तपाईंलाई हाम्रा उपलब्ध उत्पादनहरू र अर्डर प्रक्रियाको बारेमा मार्गदर्शन गर्न दिनुहोस्।"
            },
            'fallback': {
                'en': "I apologize, but I'm not sure how to help with that specific request. Let me connect you with one of our team members who can assist you better.",
                'ne': "माफ गर्नुहोस्, तर म त्यो विशेष अनुरोधमा कसरी मद्दत गर्ने भन्ने बारे निश्चित छैन। मलाई तपाईंलाई हाम्रो टोलीका सदस्यहरू मध्ये एकसँग जोड्न दिनुहोस् जसले तपाईंलाई राम्रो सहायता गर्न सक्छ।"
            }
        }
    
    def get_ai_response(self, 
                       message: str, 
                       language: str = 'en',
                       system_prompt: Optional[str] = None,
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get AI response with learning and context awareness.
        
        Args:
            message: User message
            language: Detected language
            system_prompt: Custom system prompt
            context: Additional context including conversation history
            
        Returns:
            Dict with response, confidence, source, etc.
        """
        try:
            start_time = datetime.utcnow()
            
            # Refresh learning cache if needed
            self._refresh_learning_cache_if_needed()
            
            # Check for learned responses first
            learned_response = self._check_learned_responses(message, language)
            if learned_response:
                return {
                    'success': True,
                    'response': learned_response['response'],
                    'confidence': learned_response['confidence'],
                    'source': 'learned',
                    'learning_match_id': learned_response['learning_id'],
                    'response_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    'model_used': 'learned_response'
                }
            
            # Get context-aware response from Gemini
            ai_response = self._get_gemini_response(message, language, system_prompt, context)
            
            if ai_response['success']:
                # Enhance response with business context
                enhanced_response = self._enhance_response_with_context(ai_response['response'], language, context)
                
                return {
                    'success': True,
                    'response': enhanced_response,
                    'confidence': ai_response.get('confidence', 0.8),
                    'source': 'ai_enhanced',
                    'response_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    'model_used': self.model,
                    'tokens_used': ai_response.get('tokens_used', 0)
                }
            else:
                # Return fallback response
                return self._get_fallback_response(language, start_time)
                
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            return self._get_fallback_response(language, start_time)
    
    def _get_gemini_response(self, 
                            message: str, 
                            language: str,
                            system_prompt: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get response from Google Gemini API.
        """
        try:
            # Prepare system prompt
            if not system_prompt:
                system_prompt = get_system_prompt(language)
            
            # Add learning context to system prompt
            enhanced_system_prompt = self._enhance_system_prompt_with_learning(system_prompt, language)
            
            # Prepare conversation context
            conversation_context = ""
            if context and 'conversation_history' in context:
                for hist_msg in context['conversation_history'][-5:]:  # Last 5 messages
                    role = "User" if hist_msg['role'] == 'user' else "Assistant"
                    conversation_context += f"{role}: {hist_msg['content']}\n"
            
            # Combine system prompt, conversation context, and current message
            full_prompt = f"{enhanced_system_prompt}\n\nConversation History:\n{conversation_context}\nUser: {message}\n\nAssistant:"
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.7,
                top_p=0.9,
                top_k=40
            )
            
            # Call Gemini API
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            if response.text:
                return {
                    'success': True,
                    'response': response.text.strip(),
                    'confidence': 0.8,  # Default confidence for AI responses
                    'tokens_used': 0  # Gemini doesn't provide token count in the same way
                }
            else:
                return {'success': False, 'error': 'No response from Gemini'}
                
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            return {'success': False, 'error': str(e)}
    
    def _check_learned_responses(self, message: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Check if we have a learned response for similar messages.
        """
        try:
            # Simple similarity check - in production, use more sophisticated matching
            message_lower = message.lower().strip()
            
            for learning_data in self.learning_cache.get(language, []):
                original_lower = learning_data['original_message'].lower().strip()
                
                # Simple keyword matching - enhance with semantic similarity in production
                similarity_score = self._calculate_similarity(message_lower, original_lower)
                
                if similarity_score > 0.8:  # High similarity threshold
                    return {
                        'response': learning_data['admin_correction'],
                        'confidence': min(0.95, similarity_score + 0.1),
                        'learning_id': str(learning_data['_id'])
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking learned responses: {e}")
            return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        Simple implementation - enhance with proper NLP in production.
        """
        try:
            # Simple word overlap similarity
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _enhance_system_prompt_with_learning(self, base_prompt: str, language: str) -> str:
        """
        Enhance system prompt with learned patterns and corrections.
        """
        try:
            learning_insights = self._get_learning_insights(language)
            
            if learning_insights:
                enhanced_prompt = f"{base_prompt}\n\nIMPORTANT LEARNING INSIGHTS:\n{learning_insights}"
                return enhanced_prompt
            
            return base_prompt
            
        except Exception as e:
            self.logger.error(f"Error enhancing system prompt: {e}")
            return base_prompt
    
    def _get_learning_insights(self, language: str) -> str:
        """
        Get learning insights from admin corrections.
        """
        try:
            insights = []
            
            # Get common correction patterns
            correction_patterns = self._get_correction_patterns(language)
            
            for pattern in correction_patterns[:3]:  # Top 3 patterns
                insights.append(f"- {pattern['insight']}")
            
            return "\n".join(insights) if insights else ""
            
        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return ""
    
    def _get_correction_patterns(self, language: str) -> List[Dict[str, Any]]:
        """
        Analyze admin corrections to identify patterns.
        """
        try:
            # Get recent corrections
            since = datetime.utcnow() - timedelta(days=30)
            
            corrections = list(mongo_db.db.ai_learning_data.find({
                'language': language,
                'created_at': {'$gte': since}
            }).sort('created_at', -1).limit(50))
            
            patterns = []
            
            # Analyze correction categories
            category_counts = {}
            for correction in corrections:
                category = correction.get('improvement_category', 'general')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Generate insights based on patterns
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                if count >= 3:  # At least 3 corrections in this category
                    insight = self._generate_category_insight(category, corrections)
                    if insight:
                        patterns.append({
                            'category': category,
                            'count': count,
                            'insight': insight
                        })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error getting correction patterns: {e}")
            return []
    
    def _generate_category_insight(self, category: str, corrections: List[Dict]) -> str:
        """
        Generate insight for a specific correction category.
        """
        category_insights = {
            'tone': "Use a more friendly and welcoming tone when responding to customers.",
            'accuracy': "Ensure all product information and prices are accurate and up-to-date.",
            'completeness': "Provide complete information and ask follow-up questions when needed.",
            'cultural': "Be mindful of cultural context and local preferences in responses.",
            'language': "Use appropriate language level and avoid overly technical terms.",
            'product_knowledge': "Demonstrate deep knowledge of meat products and preparation methods.",
            'ordering_process': "Clearly explain the ordering process and delivery options."
        }
        
        return category_insights.get(category, f"Pay attention to {category}-related aspects in responses.")
    
    def _enhance_response_with_context(self, response: str, language: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Enhance AI response with business-specific context.
        """
        try:
            # Add business context if response seems generic
            if self._is_generic_response(response):
                business_context = self._get_business_context(language)
                if business_context:
                    response = f"{response}\n\n{business_context}"
            
            # Add call-to-action if appropriate
            if self._should_add_cta(response, context):
                cta = self._get_appropriate_cta(language)
                if cta:
                    response = f"{response}\n\n{cta}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error enhancing response: {e}")
            return response
    
    def _is_generic_response(self, response: str) -> bool:
        """
        Check if response is too generic and needs business context.
        """
        generic_indicators = [
            "i can help", "how can i assist", "what would you like",
            "please let me know", "feel free to ask"
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in generic_indicators)
    
    def _get_business_context(self, language: str) -> str:
        """
        Get business-specific context to add to responses.
        """
        business_contexts = {
            'en': "At Nepal Meat Shop, we offer fresh, high-quality meat products with home delivery service in Kathmandu.",
            'ne': "नेपाल मीट शपमा, हामी काठमाडौंमा घर डेलिभरी सेवाको साथ ताजा, उच्च गुणस्तरका मासु उत्पादनहरू प्रदान गर्छौं।"
        }
        
        return business_contexts.get(language, business_contexts['en'])
    
    def _should_add_cta(self, response: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if a call-to-action should be added.
        """
        # Add CTA if response doesn't already have one and conversation is new
        has_cta = any(phrase in response.lower() for phrase in [
            "order", "buy", "purchase", "contact", "call", "visit"
        ])
        
        is_new_conversation = True
        if context and 'conversation_history' in context:
            is_new_conversation = len(context['conversation_history']) <= 2
        
        return not has_cta and is_new_conversation
    
    def _get_appropriate_cta(self, language: str) -> str:
        """
        Get appropriate call-to-action based on language.
        """
        ctas = {
            'en': "Would you like to browse our products or place an order?",
            'ne': "के तपाईं हाम्रा उत्पादनहरू हेर्न वा अर्डर गर्न चाहनुहुन्छ?"
        }
        
        return ctas.get(language, ctas['en'])
    
    def _get_fallback_response(self, language: str, start_time: datetime) -> Dict[str, Any]:
        """
        Get fallback response when AI fails.
        """
        fallback_text = self.response_templates['fallback'].get(language, 
                                                               self.response_templates['fallback']['en'])
        
        return {
            'success': True,
            'response': fallback_text,
            'confidence': 0.5,
            'source': 'fallback',
            'response_time_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000),
            'model_used': 'fallback'
        }
    
    def _refresh_learning_cache_if_needed(self):
        """
        Refresh learning cache if it's stale.
        """
        try:
            if datetime.utcnow() - self.last_cache_refresh > self.cache_refresh_interval:
                self._refresh_learning_cache()
                self.last_cache_refresh = datetime.utcnow()
        except Exception as e:
            self.logger.error(f"Error refreshing learning cache: {e}")
    
    def _refresh_learning_cache(self):
        """
        Refresh the learning cache with recent admin corrections.
        """
        try:
            # Get recent learning data
            since = datetime.utcnow() - timedelta(days=30)
            
            learning_data = list(mongo_db.db.ai_learning_data.find({
                'created_at': {'$gte': since},
                'confidence_improvement': {'$gte': 0.1}  # Only significant improvements
            }).sort('created_at', -1).limit(100))
            
            # Group by language
            self.learning_cache = {}
            for data in learning_data:
                language = data.get('language', 'en')
                if language not in self.learning_cache:
                    self.learning_cache[language] = []
                self.learning_cache[language].append(data)
            
            self.logger.info(f"Refreshed learning cache with {len(learning_data)} entries")
            
        except Exception as e:
            self.logger.error(f"Error refreshing learning cache: {e}")
    
    def analyze_conversation_for_learning(self, conversation_id: str) -> Dict[str, Any]:
        """
        Analyze a conversation to identify learning opportunities.
        """
        try:
            # Get conversation messages
            messages = list(mongo_db.db.chat_messages_v2.find({
                'conversation_id': conversation_id
            }).sort('timestamp', 1))
            
            analysis = {
                'conversation_id': conversation_id,
                'total_messages': len(messages),
                'ai_messages': 0,
                'admin_corrections': 0,
                'customer_satisfaction_indicators': [],
                'improvement_opportunities': [],
                'language_consistency': True,
                'response_time_analysis': []
            }
            
            prev_timestamp = None
            detected_language = None
            
            for msg in messages:
                # Count message types
                if msg['message_type'] == MessageType.AI.value:
                    analysis['ai_messages'] += 1
                    
                    # Check for admin corrections
                    if msg.get('admin_override'):
                        analysis['admin_corrections'] += 1
                    
                    # Analyze response time
                    if prev_timestamp:
                        response_time = (msg['timestamp'] - prev_timestamp).total_seconds()
                        analysis['response_time_analysis'].append(response_time)
                
                # Check language consistency
                msg_language = msg.get('language_detected')
                if msg_language:
                    if detected_language is None:
                        detected_language = msg_language
                    elif detected_language != msg_language:
                        analysis['language_consistency'] = False
                
                # Look for satisfaction indicators
                content_lower = msg['content'].lower()
                if any(word in content_lower for word in ['thank', 'thanks', 'good', 'great', 'excellent']):
                    analysis['customer_satisfaction_indicators'].append('positive')
                elif any(word in content_lower for word in ['bad', 'poor', 'terrible', 'wrong', 'confused']):
                    analysis['customer_satisfaction_indicators'].append('negative')
                
                prev_timestamp = msg['timestamp']
            
            # Calculate metrics
            if analysis['response_time_analysis']:
                analysis['avg_response_time'] = sum(analysis['response_time_analysis']) / len(analysis['response_time_analysis'])
                analysis['max_response_time'] = max(analysis['response_time_analysis'])
            
            # Identify improvement opportunities
            if analysis['admin_corrections'] > 0:
                analysis['improvement_opportunities'].append('ai_accuracy')
            
            if analysis.get('avg_response_time', 0) > 10:  # More than 10 seconds
                analysis['improvement_opportunities'].append('response_speed')
            
            if not analysis['language_consistency']:
                analysis['improvement_opportunities'].append('language_consistency')
            
            negative_indicators = analysis['customer_satisfaction_indicators'].count('negative')
            if negative_indicators > 0:
                analysis['improvement_opportunities'].append('customer_satisfaction')
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing conversation for learning: {e}")
            return {'error': str(e)}
    
    def get_learning_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get learning statistics for the specified period.
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get learning data
            learning_data = list(mongo_db.db.ai_learning_data.find({
                'created_at': {'$gte': since}
            }))
            
            # Get AI messages with corrections
            corrected_messages = list(mongo_db.db.chat_messages_v2.find({
                'timestamp': {'$gte': since},
                'message_type': MessageType.AI.value,
                'admin_override': True
            }))
            
            # Calculate statistics
            stats = {
                'period_days': days,
                'total_learning_entries': len(learning_data),
                'total_corrections': len(corrected_messages),
                'languages': {},
                'improvement_categories': {},
                'correction_trends': [],
                'top_admins': {},
                'confidence_improvements': []
            }
            
            # Analyze by language
            for entry in learning_data:
                lang = entry.get('language', 'unknown')
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            # Analyze by improvement category
            for entry in learning_data:
                category = entry.get('improvement_category', 'general')
                stats['improvement_categories'][category] = stats['improvement_categories'].get(category, 0) + 1
            
            # Analyze by admin
            for entry in learning_data:
                admin_name = entry.get('admin_name', 'unknown')
                stats['top_admins'][admin_name] = stats['top_admins'].get(admin_name, 0) + 1
            
            # Calculate confidence improvements
            for entry in learning_data:
                if 'confidence_improvement' in entry:
                    stats['confidence_improvements'].append(entry['confidence_improvement'])
            
            if stats['confidence_improvements']:
                stats['avg_confidence_improvement'] = sum(stats['confidence_improvements']) / len(stats['confidence_improvements'])
                stats['max_confidence_improvement'] = max(stats['confidence_improvements'])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {e}")
            return {'error': str(e)}

# Global service instance
enhanced_ai_service = None

def init_enhanced_ai_service(api_key: str, model: str = "gemini-1.5-flash"):
    """Initialize the enhanced AI service."""
    global enhanced_ai_service
    enhanced_ai_service = EnhancedAIService(api_key, model)
    return enhanced_ai_service

def get_enhanced_ai_service() -> Optional[EnhancedAIService]:
    """Get the global enhanced AI service instance."""
    return enhanced_ai_service