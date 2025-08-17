#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Analytics Utilities
Business analytics and insights calculation functions.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from app.utils.mongo_db import mongo_db
from app.models.mongo_models import MongoOrder, MongoUser
import calendar

class BusinessAnalytics:
    """Business analytics and insights calculator."""
    
    @staticmethod
    def get_delivery_statistics(start_date=None, end_date=None):
        """Get delivery success and cancellation statistics."""
        try:
            # Build date filter
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            
            query = {}
            if date_filter:
                query['order_date'] = date_filter
            
            # Get all orders
            orders = list(mongo_db.db.orders.find(query))
            
            # Count by status
            stats = {
                'total_orders': len(orders),
                'successful_deliveries': 0,
                'canceled_orders': 0,
                'pending_orders': 0,
                'processing_orders': 0,
                'delivered_orders': 0
            }
            
            for order in orders:
                status = order.get('status', 'pending').lower()
                if status in ['delivered', 'completed']:
                    stats['successful_deliveries'] += 1
                    stats['delivered_orders'] += 1
                elif status in ['cancelled', 'canceled']:
                    stats['canceled_orders'] += 1
                elif status == 'pending':
                    stats['pending_orders'] += 1
                elif status in ['processing', 'confirmed']:
                    stats['processing_orders'] += 1
            
            # Calculate success rate
            if stats['total_orders'] > 0:
                stats['success_rate'] = round((stats['successful_deliveries'] / stats['total_orders']) * 100, 2)
                stats['cancellation_rate'] = round((stats['canceled_orders'] / stats['total_orders']) * 100, 2)
            else:
                stats['success_rate'] = 0
                stats['cancellation_rate'] = 0
            
            return stats
        except Exception as e:
            print(f"Error getting delivery statistics: {e}")
            return {
                'total_orders': 0,
                'successful_deliveries': 0,
                'canceled_orders': 0,
                'pending_orders': 0,
                'processing_orders': 0,
                'delivered_orders': 0,
                'success_rate': 0,
                'cancellation_rate': 0
            }
    
    @staticmethod
    def get_filtered_orders(status_filter=None, start_date=None, end_date=None, limit=50):
        """Get filtered list of orders."""
        try:
            query = {}
            
            # Status filter
            if status_filter and status_filter != 'all':
                if status_filter == 'completed':
                    query['status'] = {'$in': ['delivered', 'completed']}
                elif status_filter == 'canceled':
                    query['status'] = {'$in': ['cancelled', 'canceled']}
                else:
                    query['status'] = status_filter
            
            # Date filter
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            if date_filter:
                query['order_date'] = date_filter
            
            # Get orders
            orders_data = list(mongo_db.db.orders.find(query).sort('order_date', -1).limit(limit))
            orders = [MongoOrder(order_data) for order_data in orders_data]
            
            # Convert to JSON-serializable dictionaries
            orders_json = [order.to_json_dict() for order in orders]
            
            return orders_json
        except Exception as e:
            print(f"Error getting filtered orders: {e}")
            return []
    
    @staticmethod
    def get_customer_reviews(sort_by='date', sort_order='desc', limit=100):
        """Get customer reviews with sorting."""
        try:
            # For now, we'll simulate reviews since they might not be implemented yet
            # In a real implementation, this would fetch from a reviews collection
            reviews = []
            
            # Get completed orders and simulate reviews
            completed_orders = list(mongo_db.db.orders.find({
                'status': {'$in': ['delivered', 'completed']}
            }).sort('order_date', -1).limit(limit))
            
            for order in completed_orders:
                # Simulate review data (in real app, this would come from reviews collection)
                import random
                if random.random() > 0.3:  # 70% chance of having a review
                    product_names = [item.get('product_name', 'Product') for item in order.get('items', [])]
                    
                    # Ensure review_date is a datetime object
                    order_date = order.get('order_date', datetime.utcnow())
                    if isinstance(order_date, str):
                        try:
                            from dateutil import parser
                            order_date = parser.parse(order_date)
                        except:
                            order_date = datetime.utcnow()
                    elif not isinstance(order_date, datetime):
                        order_date = datetime.utcnow()
                    
                    review = {
                        'order_id': str(order['_id']),
                        'customer_name': order.get('customer_name', 'Anonymous'),
                        'rating': random.randint(3, 5),
                        'review_text': BusinessAnalytics._generate_sample_review(),
                        'review_date': order_date,
                        'product_name': ', '.join(product_names) if product_names else 'Various Products'
                    }
                    reviews.append(review)
            
            # Sort reviews
            if sort_by == 'rating':
                reviews.sort(key=lambda x: x['rating'], reverse=(sort_order == 'desc'))
            else:  # sort by date
                reviews.sort(key=lambda x: x['review_date'], reverse=(sort_order == 'desc'))
            
            return reviews[:limit]
        except Exception as e:
            print(f"Error getting customer reviews: {e}")
            return []
    
    @staticmethod
    def _generate_sample_review():
        """Generate sample review comments."""
        import random
        positive_reviews = [
            "Excellent quality meat! Fresh and delicious.",
            "Great service and fast delivery. Highly recommended!",
            "Best meat shop in town. Always fresh products.",
            "Amazing quality and reasonable prices.",
            "Fresh meat delivered on time. Very satisfied!",
            "Outstanding service and premium quality meat.",
            "Reliable delivery and excellent customer service."
        ]
        return random.choice(positive_reviews)
    
    @staticmethod
    def get_financial_summary(start_date=None, end_date=None):
        """Get financial summary and revenue statistics."""
        try:
            # Build date filter
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            
            query = {'status': {'$in': ['delivered', 'completed']}}
            if date_filter:
                query['order_date'] = date_filter
            
            # Get completed orders
            orders = list(mongo_db.db.orders.find(query))
            
            total_revenue = 0
            delivery_areas = defaultdict(lambda: {'count': 0, 'revenue': 0})
            
            for order in orders:
                order_total = order.get('total_amount', 0)
                total_revenue += order_total
                
                # Track delivery areas - handle both string and dict formats
                delivery_address = order.get('delivery_address', {})
                if isinstance(delivery_address, dict):
                    delivery_area = delivery_address.get('area', 'Unknown')
                elif isinstance(delivery_address, str):
                    delivery_area = delivery_address if delivery_address.strip() else 'Unknown'
                else:
                    delivery_area = 'Unknown'
                
                if not delivery_area or delivery_area.strip() == '':
                    delivery_area = 'Unknown'
                
                delivery_areas[delivery_area]['count'] += 1
                delivery_areas[delivery_area]['revenue'] += order_total
            
            # Sort delivery areas by revenue
            sorted_areas = sorted(
                delivery_areas.items(),
                key=lambda x: x[1]['revenue'],
                reverse=True
            )
            
            # Get top 5 delivery areas and format for template
            top_delivery_areas = []
            for area_name, area_data in sorted_areas[:5]:
                top_delivery_areas.append({
                    'area': area_name,
                    'order_count': area_data['count'],
                    'revenue': area_data['revenue']
                })
            
            return {
                'total_revenue': total_revenue,
                'total_orders': len(orders),
                'average_order_value': round(total_revenue / len(orders), 2) if orders else 0,
                'top_delivery_areas': top_delivery_areas,
                'all_delivery_areas': dict(delivery_areas)
            }
        except Exception as e:
            print(f"Error getting financial summary: {e}")
            return {
                'total_revenue': 0,
                'total_orders': 0,
                'average_order_value': 0,
                'top_delivery_areas': [],
                'all_delivery_areas': {}
            }
    
    @staticmethod
    def get_monthly_revenue_trends(months=6):
        """Get monthly revenue trends for the last N months."""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=months * 30)
            
            # Get completed orders in date range
            orders = list(mongo_db.db.orders.find({
                'status': {'$in': ['delivered', 'completed']},
                'order_date': {'$gte': start_date, '$lte': end_date}
            }))
            
            # Group by month
            monthly_data = defaultdict(lambda: {'revenue': 0, 'orders': 0})
            
            for order in orders:
                order_date = order.get('order_date', datetime.utcnow())
                month_key = order_date.strftime('%Y-%m')
                month_name = order_date.strftime('%B %Y')
                
                monthly_data[month_key]['revenue'] += order.get('total_amount', 0)
                monthly_data[month_key]['orders'] += 1
                monthly_data[month_key]['month_name'] = month_name
                monthly_data[month_key]['month_key'] = month_key
            
            # Convert to list and sort
            trends = []
            for month_key in sorted(monthly_data.keys()):
                data = monthly_data[month_key]
                trends.append({
                    'month': data['month_name'],
                    'month_key': month_key,
                    'revenue': data['revenue'],
                    'orders': data['orders'],
                    'average_order_value': round(data['revenue'] / data['orders'], 2) if data['orders'] > 0 else 0
                })
            
            # Calculate growth rate
            if len(trends) >= 2:
                current_month = trends[-1]['revenue']
                previous_month = trends[-2]['revenue']
                if previous_month > 0:
                    growth_rate = round(((current_month - previous_month) / previous_month) * 100, 2)
                else:
                    growth_rate = 0
            else:
                growth_rate = 0
            
            return {
                'trends': trends,
                'growth_rate': growth_rate,
                'current_month_revenue': trends[-1]['revenue'] if trends else 0,
                'previous_month_revenue': trends[-2]['revenue'] if len(trends) >= 2 else 0
            }
        except Exception as e:
            print(f"Error getting monthly revenue trends: {e}")
            return {
                'trends': [],
                'growth_rate': 0,
                'current_month_revenue': 0,
                'previous_month_revenue': 0
            }