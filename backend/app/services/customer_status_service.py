from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
from app.utils.mongo_db import mongo_db
from app.models.enhanced_chat_v2 import ChatConversationV2
import logging

logger = logging.getLogger(__name__)

class CustomerStatusService:
    """
    Service to track customer online/offline status for admin messenger feature.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory tracking for real-time status
        self.online_customers = {}  # session_id -> customer_info
        self.customer_last_seen = {}  # session_id -> timestamp
        self.user_counter = self._initialize_user_counter()  # Counter for auto-generated user names
        
    def _initialize_user_counter(self) -> int:
        """
        Initialize the user counter based on existing display names in the database.
        
        Returns:
            Starting counter value
        """
        try:
            from app.utils.mongo_db import mongo_db
            
            # Find all conversations with auto-generated display names
            conversations = mongo_db.db.chat_conversations_v2.find({
                'display_name': {'$regex': r'^User \d+$'}
            })
            
            max_number = 0
            for conv in conversations:
                display_name = conv.get('display_name', '')
                if display_name.startswith('User '):
                    try:
                        number = int(display_name.split(' ')[1])
                        max_number = max(max_number, number)
                    except (IndexError, ValueError):
                        continue
            
            return max_number
            
        except Exception as e:
            self.logger.error(f"Error initializing user counter: {e}")
            return 0
        
    def mark_customer_online(self, session_id: str, customer_info: Dict[str, Any]) -> None:
        """
        Mark a customer as online.
        
        Args:
            session_id: Customer session ID
            customer_info: Customer information including IP, user agent, etc.
        """
        try:
            now = datetime.utcnow()
            
            # Generate display name if not provided
            display_name = customer_info.get('customer_id') or customer_info.get('display_name')
            if not display_name:
                display_name = self._generate_user_name(session_id)
            
            # Update in-memory tracking
            self.online_customers[session_id] = {
                'session_id': session_id,
                'customer_id': customer_info.get('customer_id'),
                'display_name': display_name,
                'ip_address': customer_info.get('ip_address'),
                'user_agent': customer_info.get('user_agent'),
                'page_type': customer_info.get('page_type', 'unknown'),
                'language': customer_info.get('language', 'en'),
                'first_seen': customer_info.get('first_seen', now),
                'last_seen': now,
                'status': 'online'
            }
            
            self.customer_last_seen[session_id] = now
            
            # Update database
            self._update_customer_status_db(session_id, 'online', customer_info)
            
            self.logger.info(f"Customer {session_id} ({display_name}) marked as online")
            
        except Exception as e:
            self.logger.error(f"Error marking customer online: {e}")
    
    def _generate_user_name(self, session_id: str) -> str:
        """
        Generate a sequential user name like "User 1", "User 2", etc.
        
        Args:
            session_id: Customer session ID
            
        Returns:
            Generated user name
        """
        try:
            # Check if this session already has a generated name in database
            from app.utils.mongo_db import mongo_db
            existing_conversation = mongo_db.db.chat_conversations_v2.find_one({
                'session_id': session_id
            })
            
            if existing_conversation and existing_conversation.get('display_name'):
                return existing_conversation['display_name']
            
            # Generate new user name
            self.user_counter += 1
            display_name = f"User {self.user_counter}"
            
            # Store in database for persistence
            if existing_conversation:
                mongo_db.db.chat_conversations_v2.update_one(
                    {'session_id': session_id},
                    {'$set': {'display_name': display_name}}
                )
            
            return display_name
            
        except Exception as e:
            self.logger.error(f"Error generating user name: {e}")
            return f"User {session_id[:8]}"
    
    def mark_customer_offline(self, session_id: str) -> None:
        """
        Mark a customer as offline.
        
        Args:
            session_id: Customer session ID
        """
        try:
            now = datetime.utcnow()
            
            # Update in-memory tracking
            if session_id in self.online_customers:
                self.online_customers[session_id]['status'] = 'offline'
                self.online_customers[session_id]['last_seen'] = now
                
                # Remove from online list after a delay
                # Keep in memory for a short time to show "recently offline"
                self.customer_last_seen[session_id] = now
            
            # Update database
            self._update_customer_status_db(session_id, 'offline')
            
            self.logger.info(f"Customer {session_id} marked as offline")
            
        except Exception as e:
            self.logger.error(f"Error marking customer offline: {e}")
    
    def update_customer_activity(self, session_id: str) -> None:
        """
        Update customer's last activity timestamp.
        
        Args:
            session_id: Customer session ID
        """
        try:
            now = datetime.utcnow()
            
            if session_id in self.online_customers:
                self.online_customers[session_id]['last_seen'] = now
                self.customer_last_seen[session_id] = now
                
                # Update database periodically (every 30 seconds)
                last_db_update = self.online_customers[session_id].get('last_db_update', datetime.min)
                if (now - last_db_update).total_seconds() > 30:
                    self._update_customer_status_db(session_id, 'online')
                    self.online_customers[session_id]['last_db_update'] = now
            
        except Exception as e:
            self.logger.error(f"Error updating customer activity: {e}")
    
    def get_online_customers(self) -> List[Dict[str, Any]]:
        """
        Get list of currently online customers.
        
        Returns:
            List of online customer information
        """
        try:
            now = datetime.utcnow()
            online_customers = []
            
            # Clean up offline customers (offline for more than 5 minutes)
            offline_threshold = now - timedelta(minutes=5)
            sessions_to_remove = []
            
            for session_id, customer in self.online_customers.items():
                last_seen = self.customer_last_seen.get(session_id, datetime.min)
                
                if last_seen < offline_threshold:
                    sessions_to_remove.append(session_id)
                elif customer['status'] == 'online':
                    # Get conversation info
                    conversation_info = self._get_customer_conversation_info(session_id)
                    
                    customer_data = {
                        **customer,
                        'conversation': conversation_info,
                        'time_online': self._format_time_online(customer['first_seen'], now),
                        'last_activity': self._format_last_activity(last_seen, now)
                    }
                    online_customers.append(customer_data)
            
            # Remove offline customers
            for session_id in sessions_to_remove:
                self.online_customers.pop(session_id, None)
                self.customer_last_seen.pop(session_id, None)
            
            # Sort by last activity (most recent first)
            online_customers.sort(key=lambda x: x['last_seen'], reverse=True)
            
            return online_customers
            
        except Exception as e:
            self.logger.error(f"Error getting online customers: {e}")
            return []
    
    def get_customer_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific customer's status.
        
        Args:
            session_id: Customer session ID
            
        Returns:
            Customer status information or None if not found
        """
        try:
            if session_id in self.online_customers:
                customer = self.online_customers[session_id]
                last_seen = self.customer_last_seen.get(session_id, datetime.min)
                now = datetime.utcnow()
                
                return {
                    **customer,
                    'conversation': self._get_customer_conversation_info(session_id),
                    'time_online': self._format_time_online(customer['first_seen'], now),
                    'last_activity': self._format_last_activity(last_seen, now)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting customer status: {e}")
            return None
    
    def _update_customer_status_db(self, session_id: str, status: str, customer_info: Dict[str, Any] = None) -> None:
        """
        Update customer status in database.
        """
        try:
            now = datetime.utcnow()
            
            update_data = {
                'session_id': session_id,
                'status': status,
                'last_seen': now,
                'updated_at': now
            }
            
            if customer_info:
                update_data.update({
                    'customer_id': customer_info.get('customer_id'),
                    'ip_address': customer_info.get('ip_address'),
                    'user_agent': customer_info.get('user_agent'),
                    'page_type': customer_info.get('page_type'),
                    'language': customer_info.get('language'),
                    'first_seen': customer_info.get('first_seen', now)
                })
            
            # Upsert customer status
            mongo_db.db.customer_status.update_one(
                {'session_id': session_id},
                {'$set': update_data},
                upsert=True
            )
            
        except Exception as e:
            self.logger.error(f"Error updating customer status in DB: {e}")
    
    def _get_customer_conversation_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer's conversation information.
        """
        try:
            # Get active conversation for this session
            conv_data = mongo_db.db.chat_conversations_v2.find_one({
                'session_id': session_id,
                'status': {'$in': ['active', 'admin_active']}
            })
            
            if conv_data:
                conversation = ChatConversationV2(conv_data)
                
                # Get message count
                message_count = mongo_db.db.chat_messages_v2.count_documents({
                    'conversation_id': conversation.conversation_id
                })
                
                return {
                    'conversation_id': conversation.conversation_id,
                    'status': conversation.status,
                    'is_admin_active': conversation.is_admin_active,
                    'admin_taken_by': conversation.admin_taken_by,
                    'message_count': message_count,
                    'created_at': conversation.created_at,
                    'language_detected': conversation.language_detected
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting conversation info: {e}")
            return None
    
    def _format_time_online(self, first_seen: datetime, now: datetime) -> str:
        """
        Format time online duration.
        """
        try:
            duration = now - first_seen
            
            if duration.total_seconds() < 60:
                return "Just now"
            elif duration.total_seconds() < 3600:
                minutes = int(duration.total_seconds() / 60)
                return f"{minutes}m online"
            else:
                hours = int(duration.total_seconds() / 3600)
                return f"{hours}h online"
                
        except Exception:
            return "Unknown"
    
    def _format_last_activity(self, last_seen: datetime, now: datetime) -> str:
        """
        Format last activity time.
        """
        try:
            duration = now - last_seen
            
            if duration.total_seconds() < 30:
                return "Active now"
            elif duration.total_seconds() < 60:
                return "Active 1m ago"
            elif duration.total_seconds() < 3600:
                minutes = int(duration.total_seconds() / 60)
                return f"Active {minutes}m ago"
            else:
                hours = int(duration.total_seconds() / 3600)
                return f"Active {hours}h ago"
                
        except Exception:
            return "Unknown"

# Global instance
customer_status_service = CustomerStatusService()

def get_customer_status_service() -> CustomerStatusService:
    """Get the global customer status service instance."""
    return customer_status_service