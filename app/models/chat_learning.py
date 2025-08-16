from datetime import datetime
from app.database.mongo_db import mongo_db

class MongoChatLearning:
    """
    Model for storing AI chat learning data to enable continuous improvement.
    This model tracks user interactions, patterns, and feedback to help
    the AI assistant (Ebregel) learn and improve over time.
    """
    
    def __init__(self, data=None):
        if data:
            self._id = data.get('_id')
            self.user_message = data.get('user_message')
            self.bot_reply = data.get('bot_reply')
            self.timestamp = data.get('timestamp') or datetime.utcnow()
            self.language_detected = data.get('language_detected')
            self.response_time_ms = data.get('response_time_ms')
            self.response_source = data.get('response_source', 'ai')
            self.confidence_score = data.get('confidence_score', 0.0)
            
            # Learning-specific fields
            self.keywords = data.get('keywords', [])  # Extracted keywords from user message
            self.intent = data.get('intent')  # Classified user intent
            self.context = data.get('context', {})  # Additional context information
            self.user_satisfaction = data.get('user_satisfaction')  # Inferred satisfaction level
            self.improvement_suggestions = data.get('improvement_suggestions', [])  # Areas for improvement
            
        else:
            self._id = None
            self.user_message = None
            self.bot_reply = None
            self.timestamp = datetime.utcnow()
            self.language_detected = None
            self.response_time_ms = None
            self.response_source = 'ai'
            self.confidence_score = 0.0
            self.keywords = []
            self.intent = None
            self.context = {}
            self.user_satisfaction = None
            self.improvement_suggestions = []
    
    @property
    def collection(self):
        return mongo_db.db.chat_learning
    
    def save(self):
        """Save the learning data to MongoDB"""
        try:
            learning_data = {
                'user_message': self.user_message,
                'bot_reply': self.bot_reply,
                'timestamp': self.timestamp,
                'language_detected': self.language_detected,
                'response_time_ms': self.response_time_ms,
                'response_source': self.response_source,
                'confidence_score': self.confidence_score,
                'keywords': self.keywords,
                'intent': self.intent,
                'context': self.context,
                'user_satisfaction': self.user_satisfaction,
                'improvement_suggestions': self.improvement_suggestions
            }
            
            if self._id:
                # Update existing record
                result = self.collection.update_one(
                    {'_id': self._id},
                    {'$set': learning_data}
                )
                return result.modified_count > 0
            else:
                # Insert new record
                result = self.collection.insert_one(learning_data)
                self._id = result.inserted_id
                return True
                
        except Exception as e:
            print(f"Error saving learning data: {e}")
            return False
    
    @classmethod
    def find_by_intent(cls, intent, limit=100):
        """Find learning data by intent classification"""
        try:
            cursor = mongo_db.db.chat_learning.find(
                {'intent': intent}
            ).limit(limit).sort('timestamp', -1)
            
            return [cls(data) for data in cursor]
        except Exception as e:
            print(f"Error finding learning data by intent: {e}")
            return []
    
    @classmethod
    def find_by_keywords(cls, keywords, limit=100):
        """Find learning data by keywords"""
        try:
            cursor = mongo_db.db.chat_learning.find(
                {'keywords': {'$in': keywords}}
            ).limit(limit).sort('timestamp', -1)
            
            return [cls(data) for data in cursor]
        except Exception as e:
            print(f"Error finding learning data by keywords: {e}")
            return []
    
    @classmethod
    def get_learning_stats(cls):
        """Get statistics about learning data"""
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_entries': {'$sum': 1},
                        'avg_confidence': {'$avg': '$confidence_score'},
                        'avg_response_time': {'$avg': '$response_time_ms'},
                        'intents': {'$addToSet': '$intent'},
                        'languages': {'$addToSet': '$language_detected'}
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'total_entries': 1,
                        'avg_confidence': {'$round': ['$avg_confidence', 2]},
                        'avg_response_time': {'$round': ['$avg_response_time', 2]},
                        'unique_intents': {'$size': '$intents'},
                        'unique_languages': {'$size': '$languages'},
                        'intents': 1,
                        'languages': 1
                    }
                }
            ]
            
            result = list(mongo_db.db.chat_learning.aggregate(pipeline))
            return result[0] if result else {}
            
        except Exception as e:
            print(f"Error getting learning stats: {e}")
            return {}
    
    @classmethod
    def get_recent_patterns(cls, days=7, limit=50):
        """Get recent interaction patterns for analysis"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = mongo_db.db.chat_learning.find(
                {'timestamp': {'$gte': cutoff_date}}
            ).limit(limit).sort('timestamp', -1)
            
            return [cls(data) for data in cursor]
            
        except Exception as e:
            print(f"Error getting recent patterns: {e}")
            return []