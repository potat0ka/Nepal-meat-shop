#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - AI Service Manager
Robust AI service management with retry logic, circuit breaker, caching, and fallback mechanisms.
"""

import os
import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import google.generativeai as genai
from flask import current_app

from app.utils.mongo_db import mongo_db

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class AIResponse:
    """Structured AI response with metadata."""
    content: str
    source: str  # 'ai', 'cache', 'fallback'
    language: str
    confidence: float
    response_time_ms: int
    timestamp: datetime
    cached: bool = False

class AIServiceManager:
    """
    Robust AI service manager with comprehensive error handling and reliability features.
    """
    
    def __init__(self):
        self.client = None
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.circuit_failure_threshold = 5
        self.circuit_timeout = 300  # 5 minutes
        self.cache_ttl = 3600  # 1 hour
        self.max_tokens = 500
        self.temperature = 0.7
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.cached_responses = 0
        self.fallback_responses = 0
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
    def get_gemini_client(self) -> Optional[Any]:
        """Get or create Gemini client with error handling."""
        if self.client is None:
            try:
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    self.logger.warning("GEMINI_API_KEY not found, using fallback mode")
                    return None
                    
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info("Gemini client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                return None
        return self.client
    
    def _generate_cache_key(self, message: str, language: str, system_prompt: str) -> str:
        """Generate cache key for message."""
        content = f"{message}|{language}|{system_prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        try:
            cache_collection = mongo_db.db.ai_cache
            cached = cache_collection.find_one({'cache_key': cache_key})
            
            if cached and cached.get('expires_at', datetime.utcnow()) > datetime.utcnow():
                self.cached_responses += 1
                return cached
        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, response: str, language: str, confidence: float):
        """Save response to cache."""
        try:
            cache_collection = mongo_db.db.ai_cache
            cache_data = {
                'cache_key': cache_key,
                'response': response,
                'language': language,
                'confidence': confidence,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(seconds=self.cache_ttl),
                'hit_count': 1
            }
            cache_collection.replace_one(
                {'cache_key': cache_key},
                cache_data,
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Cache save error: {e}")
    
    def _update_cache_hit(self, cache_key: str):
        """Update cache hit count."""
        try:
            cache_collection = mongo_db.db.ai_cache
            cache_collection.update_one(
                {'cache_key': cache_key},
                {'$inc': {'hit_count': 1}}
            )
        except Exception as e:
            self.logger.error(f"Cache hit update error: {e}")
    
    def _get_fallback_response(self, message: str, language: str, context: Dict[str, Any] = None) -> str:
        """Generate intelligent fallback response based on message content and context."""
        self.fallback_responses += 1
        
        # Analyze message for intent
        message_lower = message.lower()
        
        # Product inquiry responses
        if any(word in message_lower for word in ['price', 'cost', 'rate', 'paisa', 'rupiya', 'kati']):
            if language == 'nepali_devanagari':
                return "नमस्ते! मूल्यहरूको बारेमा जानकारीको लागि कृपया हाम्रो वेबसाइट हेर्नुहोस् वा फोन गर्नुहोस्। म Ebregel हुँ, तपाईंको सहायक।"
            elif language == 'nepali_romanized':
                return "Namaste! Mulyaharu ko bare ma jankari ko lagi kripaya hamro website hernuhos wa phone garnuhos. Ma Ebregel hun, tapai ko sahayak."
            else:
                return "Hello! For current pricing information, please check our website or give us a call. I'm Ebregel, your assistant at Nepal Meat Shop."
        
        # Delivery inquiry responses
        elif any(word in message_lower for word in ['delivery', 'deliver', 'order', 'pathau']):
            if language == 'nepali_devanagari':
                return "हामी काठमाडौं उपत्यकामा २-४ घण्टामा डिलिभरी गर्छौं। अर्डरको लागि वेबसाइट प्रयोग गर्नुहोस्। म Ebregel हुँ।"
            elif language == 'nepali_romanized':
                return "Hami Kathmandu upatyaka ma 2-4 ghanta ma delivery garchhaun. Order ko lagi website prayog garnuhos. Ma Ebregel hun."
            else:
                return "We deliver within Kathmandu valley in 2-4 hours. You can place orders through our website. I'm Ebregel, here to help!"
        
        # Product availability responses
        elif any(word in message_lower for word in ['chicken', 'mutton', 'fish', 'meat', 'masu', 'kukhura', 'khasi']):
            if language == 'nepali_devanagari':
                return "हामीसँग ताजा कुखुरा, खसी, माछा र अन्य मासुहरू छन्। उपलब्धताको लागि वेबसाइट हेर्नुहोस्। म Ebregel हुँ।"
            elif language == 'nepali_romanized':
                return "Hami sanga taja kukhura, khasi, machha ra anya masuharu chhan. Upalabdhata ko lagi website hernuhos. Ma Ebregel hun."
            else:
                return "We have fresh chicken, mutton, fish, and other premium meats available. Check our website for current availability. I'm Ebregel!"
        
        # Greeting responses
        elif any(word in message_lower for word in ['hello', 'hi', 'namaste', 'hey']):
            if language == 'nepali_devanagari':
                return "नमस्ते! म Ebregel हुँ, नेपाल मीट शपको AI सहायक। म तपाईंलाई कसरी मद्दत गर्न सक्छु?"
            elif language == 'nepali_romanized':
                return "Namaste! Ma Ebregel hun, Nepal Meat Shop ko AI sahayak. Ma tapai lai kasari maddat garna sakchhu?"
            else:
                return "Hello! I'm Ebregel, your AI assistant at Nepal Meat Shop. How can I help you today?"
        
        # Default responses
        else:
            if language == 'nepali_devanagari':
                return "म Ebregel हुँ। अहिले AI सेवामा समस्या छ, तर म तपाईंलाई मद्दत गर्न चाहन्छु। कृपया वेबसाइट हेर्नुहोस् वा फोन गर्नुहोस्।"
            elif language == 'nepali_romanized':
                return "Ma Ebregel hun. Ahile AI seva ma samasya chha, tara ma tapai lai maddat garna chhanchu. Kripaya website hernuhos wa phone garnuhos."
            else:
                return "I'm Ebregel, your assistant at Nepal Meat Shop. I'm experiencing some technical difficulties right now, but I'm here to help! Please check our website or give us a call for immediate assistance."
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_state == CircuitState.OPEN:
            if self.last_failure_time and \
               (datetime.utcnow() - self.last_failure_time).total_seconds() > self.circuit_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker moved to HALF_OPEN state")
                return False
            return True
        return False
    
    def _record_success(self):
        """Record successful API call."""
        self.successful_requests += 1
        self.success_count += 1
        self.failure_count = 0
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.logger.info("Circuit breaker CLOSED after successful request")
    
    def _record_failure(self):
        """Record failed API call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.circuit_failure_threshold:
            self.circuit_state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
    
    def _call_gemini_with_retry(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call Gemini API with retry logic."""
        client = self.get_gemini_client()
        if not client:
            return None
        
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is OPEN, skipping API call")
            return None
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Convert messages to Gemini format
                prompt = ""
                for msg in messages:
                    if msg["role"] == "system":
                        prompt += f"System: {msg['content']}\n\n"
                    elif msg["role"] == "user":
                        prompt += f"User: {msg['content']}\n\n"
                
                response = client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                )
                
                content = response.text.strip()
                self._record_success()
                return content
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                else:
                    self._record_failure()
        
        self.logger.error(f"All Gemini API attempts failed. Last error: {last_exception}")
        return None
    
    def get_ai_response(self, message: str, language: str, system_prompt: str, 
                      context: Dict[str, Any] = None) -> AIResponse:
        """Get AI response with full reliability features."""
        start_time = time.time()
        self.total_requests += 1
        
        # Generate cache key
        cache_key = self._generate_cache_key(message, language, system_prompt)
        
        # Try cache first
        cached = self._get_cached_response(cache_key)
        if cached:
            self._update_cache_hit(cache_key)
            response_time = int((time.time() - start_time) * 1000)
            return AIResponse(
                content=cached['response'],
                source='cache',
                language=language,
                confidence=cached.get('confidence', 0.9),
                response_time_ms=response_time,
                timestamp=datetime.utcnow(),
                cached=True
            )
        
        # Try AI service
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        ai_response = self._call_gemini_with_retry(messages)
        
        if ai_response:
            # Save to cache
            self._save_to_cache(cache_key, ai_response, language, 0.95)
            
            response_time = int((time.time() - start_time) * 1000)
            return AIResponse(
                content=ai_response,
                source='ai',
                language=language,
                confidence=0.95,
                response_time_ms=response_time,
                timestamp=datetime.utcnow()
            )
        
        # Fallback response
        fallback_content = self._get_fallback_response(message, language, context)
        response_time = int((time.time() - start_time) * 1000)
        
        return AIResponse(
            content=fallback_content,
            source='fallback',
            language=language,
            confidence=0.7,
            response_time_ms=response_time,
            timestamp=datetime.utcnow()
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        success_rate = (self.successful_requests / max(self.total_requests, 1)) * 100
        cache_hit_rate = (self.cached_responses / max(self.total_requests, 1)) * 100
        fallback_rate = (self.fallback_responses / max(self.total_requests, 1)) * 100
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'cached_responses': self.cached_responses,
            'fallback_responses': self.fallback_responses,
            'success_rate': round(success_rate, 2),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'fallback_rate': round(fallback_rate, 2),
            'circuit_state': self.circuit_state.value,
            'failure_count': self.failure_count
        }
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed service statistics for admin dashboard."""
        basic_stats = self.get_stats()
        
        # Add detailed information
        detailed_stats = {
            **basic_stats,
            'configuration': {
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'circuit_failure_threshold': self.circuit_failure_threshold,
                'circuit_timeout': self.circuit_timeout,
                'cache_ttl': self.cache_ttl,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature
            },
            'circuit_breaker': {
                'state': self.circuit_state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
            },
            'performance': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'cached_responses': self.cached_responses,
                'fallback_responses': self.fallback_responses
            }
        }
        
        # Add cache statistics
        try:
            cache_stats = mongo_db.db.ai_cache.aggregate([
                {
                    '$group': {
                        '_id': None,
                        'total_entries': {'$sum': 1},
                        'total_hits': {'$sum': '$hit_count'},
                        'avg_confidence': {'$avg': '$confidence'}
                    }
                }
            ])
            cache_result = list(cache_stats)
            if cache_result:
                detailed_stats['cache_statistics'] = cache_result[0]
            else:
                detailed_stats['cache_statistics'] = {
                    'total_entries': 0,
                    'total_hits': 0,
                    'avg_confidence': 0
                }
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            detailed_stats['cache_statistics'] = {'error': 'Failed to retrieve cache stats'}
        
        return detailed_stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            'all_services_ok': True,
            'services': {},
            'fallback_available': True
        }
        
        # Check Gemini client
        try:
            client = self.get_gemini_client()
            if client:
                health_status['services']['gemini'] = {
                    'status': 'healthy',
                    'circuit_state': self.circuit_state.value
                }
            else:
                health_status['services']['gemini'] = {
                    'status': 'unavailable',
                    'circuit_state': self.circuit_state.value
                }
                health_status['all_services_ok'] = False
        except Exception as e:
            health_status['services']['gemini'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['all_services_ok'] = False
        
        # Check MongoDB connection
        try:
            mongo_db.db.command('ping')
            health_status['services']['mongodb'] = {'status': 'healthy'}
        except Exception as e:
            health_status['services']['mongodb'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['all_services_ok'] = False
        
        # Check cache functionality
        try:
            test_key = 'health_check_test'
            mongo_db.db.ai_cache.find_one({'cache_key': test_key})
            health_status['services']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health_status['services']['cache'] = {
                'status': 'error',
                'error': str(e)
            }
            # Cache failure doesn't break the service
        
        return health_status
    
    def clear_cache(self, older_than_hours: int = 24):
        """Clear old cache entries."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            result = mongo_db.db.ai_cache.delete_many({
                'created_at': {'$lt': cutoff_time}
            })
            self.logger.info(f"Cleared {result.deleted_count} old cache entries")
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")

# Global instance
ai_service = AIServiceManager()