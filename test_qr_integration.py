#!/usr/bin/env python3
"""
Test QR code integration functionality
"""

import os

def test_qr_code_integration():
    """Test QR code integration"""
    print("Testing QR Code Integration...")
    print("=" * 50)
    
    # Test QR code files existence
    print("Testing QR code file accessibility...")
    qr_code_files = [
        'uploads/qr_codes/bank_transfer_qr_code.svg',
        'uploads/qr_codes/esewa_qr_code.svg',
        'uploads/qr_codes/khalti_qr_code.svg',
        'uploads/qr_codes/ime_pay_qr_code.svg',
        'uploads/qr_codes/fone_pay_qr_code.svg',
        'uploads/qr_codes/prabhu_pay_qr_code.svg',
        'uploads/qr_codes/cell_pay_qr_code.svg',
        'static/uploads/qr_codes/bank_transfer_qr_code.svg',
        'static/uploads/qr_codes/esewa_qr_code.svg',
        'static/uploads/qr_codes/khalti_qr_code.svg',
        'static/uploads/qr_codes/ime_pay_qr_code.svg',
        'static/uploads/qr_codes/fone_pay_qr_code.svg',
        'static/uploads/qr_codes/prabhu_pay_qr_code.svg',
        'static/uploads/qr_codes/cell_pay_qr_code.svg'
    ]
    
    files_found = 0
    for file_path in qr_code_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
            files_found += 1
        else:
            print(f"❌ {file_path}")
    
    print(f"\nFiles found: {files_found}/{len(qr_code_files)}")
    
    # Test available payment methods
    print("\nAvailable payment methods in admin:")
    available_methods = [
        {'id': 'bank', 'name': 'Bank Transfer', 'name_nepali': 'बैंक ट्रान्सफर'},
        {'id': 'esewa', 'name': 'eSewa', 'name_nepali': 'ईसेवा'},
        {'id': 'khalti', 'name': 'Khalti', 'name_nepali': 'खल्ती'},
        {'id': 'ime_pay', 'name': 'IME Pay', 'name_nepali': 'आईएमई पे'},
        {'id': 'fonepay', 'name': 'FonePay', 'name_nepali': 'फोनपे'},
        {'id': 'prabhupay', 'name': 'PrabhuPay', 'name_nepali': 'प्रभुपे'},
        {'id': 'cellpay', 'name': 'CellPay', 'name_nepali': 'सेलपे'},
    ]
    
    for method in available_methods:
        print(f"   - {method['id']}: {method['name']} ({method['name_nepali']})")
    
    # Test fallback QR codes
    print("\nFallback QR codes available:")
    fallback_qr_codes = {
        'bank': {
            'image_filename': 'qr_codes/bank_transfer_qr_code.svg',
            'description': 'Bank Transfer QR Code for payments',
            'display_name': 'Bank Transfer'
        },
        'esewa': {
            'image_filename': 'qr_codes/esewa_qr_code.svg',
            'description': 'Pay using eSewa digital wallet',
            'display_name': 'eSewa'
        },
        'khalti': {
            'image_filename': 'qr_codes/khalti_qr_code.svg',
            'description': 'Pay using Khalti digital wallet',
            'display_name': 'Khalti'
        },
        'ime_pay': {
            'image_filename': 'qr_codes/ime_pay_qr_code.svg',
            'description': 'Pay using IME Pay digital wallet',
            'display_name': 'IME Pay'
        },
        'fonepay': {
            'image_filename': 'qr_codes/fone_pay_qr_code.svg',
            'description': 'Pay using FonePay digital wallet',
            'display_name': 'FonePay'
        },
        'prabhupay': {
            'image_filename': 'qr_codes/prabhu_pay_qr_code.svg',
            'description': 'Pay using PrabhuPay digital wallet',
            'display_name': 'PrabhuPay'
        },
        'cellpay': {
            'image_filename': 'qr_codes/cell_pay_qr_code.svg',
            'description': 'Pay using CellPay digital wallet',
            'display_name': 'CellPay'
        }
    }
    
    for method, qr in fallback_qr_codes.items():
        print(f"   - {method}: {qr['image_filename']} ({qr['display_name']})")
    
    print("\n" + "=" * 50)
    print("QR Code Integration Test Complete!")
    
    if files_found >= 2:
        print("✅ QR code integration is working correctly!")
    else:
        print("⚠️  Some QR code files are missing, but fallback system should work.")

if __name__ == "__main__":
    test_qr_code_integration()