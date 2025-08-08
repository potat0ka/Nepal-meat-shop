#!/usr/bin/env python3
"""
🍖 Nepal Meat Shop - Payment System Test
Test script to verify payment gateway functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv('.env.mongo')

def test_payment_gateways():
    """Test payment gateway initialization and configuration."""
    print("🧪 Testing Payment Gateway System")
    print("=" * 50)
    
    try:
        # Import payment manager
        from app.services.gateways import payment_manager
        
        print("✅ Payment manager imported successfully")
        
        # Test gateway availability
        available_gateways = payment_manager.get_available_gateways()
        print(f"📱 Available gateways: {len(available_gateways)}")
        
        for gateway in available_gateways:
            print(f"   - {gateway['display_name']}: {gateway['description']}")
        
        # Test gateway configuration
        print("\n🔧 Gateway Configuration Status:")
        try:
            status = payment_manager.get_all_gateway_status()
            print(f"  Gateway status: {status.get('configured_gateways', 0)}/{status.get('total_gateways', 0)} configured")
            
            for gateway_name, gateway_status in status.get('gateways', {}).items():
                if isinstance(gateway_status, dict):
                    configured = gateway_status.get('configured', False)
                    display_name = gateway_name.title()
                    print(f"    {display_name}: {'✅ Ready' if configured else '❌ Not configured'}")
                else:
                    print(f"    {gateway_name}: ❌ Invalid status data")
        except Exception as e:
            print(f"  Error getting gateway status: {str(e)}")
        
        # Test individual gateways
        print("\n🧪 Testing Individual Gateways:")
        
        # Test Khalti
        try:
            khalti_status = payment_manager.get_gateway_status('khalti')
            print(f"   - Khalti: {'✅ Ready' if khalti_status['configured'] else '❌ Not Ready'}")
            if khalti_status['configured']:
                print(f"     Environment: {khalti_status.get('environment', 'Unknown')}")
        except Exception as e:
            print(f"   - Khalti: ❌ Error - {str(e)}")
        
        # Test eSewa
        try:
            esewa_status = payment_manager.get_gateway_status('esewa')
            print(f"   - eSewa: {'✅ Ready' if esewa_status['configured'] else '❌ Not Ready'}")
            if esewa_status['configured']:
                print(f"     Environment: {esewa_status.get('environment', 'Unknown')}")
        except Exception as e:
            print(f"   - eSewa: ❌ Error - {str(e)}")
        
        # Test payment initiation (mock)
        print("\n💳 Testing Payment Initiation:")
        test_payment_data = {
            'amount': 1000,
            'order_id': 'TEST_ORDER_123',
            'customer_info': {
                'name': 'Test Customer',
                'email': 'test@example.com',
                'phone': '9800000000'
            },
            'return_url': 'http://localhost:5000/payment/success',
            'website_url': 'http://localhost:5000'
        }
        
        for gateway_name in ['khalti', 'esewa']:
            try:
                if payment_manager.is_gateway_available(gateway_name):
                    result = payment_manager.initiate_payment(
                        gateway_name=gateway_name,
                        amount=test_payment_data['amount'],
                        order_number=test_payment_data['order_id'],
                        customer_info=test_payment_data['customer_info']
                    )
                    print(f"   - {gateway_name.title()}: ✅ Initiation successful")
                    print(f"     Payment URL: {result.get('payment_url', 'N/A')}")
                else:
                    print(f"   - {gateway_name.title()}: ⚠️ Gateway not available")
            except Exception as e:
                print(f"   - {gateway_name.title()}: ❌ Error - {str(e)}")
        
        print("\n🎉 Payment system test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure the payment gateway system is properly installed.")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def test_environment_variables():
    """Test if required environment variables are set."""
    print("\n🔍 Checking Environment Variables:")
    print("=" * 50)
    
    required_vars = [
        'KHALTI_ENABLED',
        'KHALTI_ENVIRONMENT',
        'KHALTI_PUBLIC_KEY',
        'KHALTI_SECRET_KEY',
        'ESEWA_ENABLED',
        'ESEWA_ENVIRONMENT',
        'ESEWA_MERCHANT_CODE',
        'ESEWA_SECRET_KEY'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if 'SECRET' in var or 'KEY' in var:
                display_value = f"{value[:4]}***{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")

def main():
    """Main test function."""
    print("🍖 Nepal Meat Shop - Payment System Test")
    print("=" * 60)
    
    # Test environment variables
    test_environment_variables()
    
    # Test payment gateways
    test_payment_gateways()
    
    print("\n" + "=" * 60)
    print("Test completed! Check the results above.")

if __name__ == '__main__':
    main()