#!/usr/bin/env python3
"""
Check QR codes in the database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.mongo_db import mongo_db

try:
    # Check QR codes
    qr_codes = list(mongo_db.db.qr_codes.find({}))
    print(f"Found {len(qr_codes)} QR codes:")
    
    for qr in qr_codes:
        print(f"- {qr['payment_method']}: {qr['qr_image']}")
        print(f"  Display name: {qr.get('display_name', 'N/A')}")
        print(f"  Description: {qr.get('description', 'N/A')}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()