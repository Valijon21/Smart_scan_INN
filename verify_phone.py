
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add current dir to path
sys.path.append(os.getcwd())

from app.ocr_service import search_organizations, lookup_company_by_inn

def test_phone_extraction():
    print("Testing Phone Extraction...")
    
    # Test 1: Search by Name "Chinor MFY"
    print("\n--- Test 1: Search 'Chinor' ---")
    results = search_organizations("Chinor")
    found = False
    for res in results:
        if "Chinor" in res['name']:
            print(f"PASS: Found {res['name']}")
            print(f"Phone: {res.get('phone')}")
            if res.get('phone'):
                print("PASS: Phone number is present")
                found = True
            else:
                print("FAIL: Phone number is MISSING")
            break
    if not found:
        print("FAIL: Chinor MFY not found in search")

    # Test 2: Lookup by INN (Using Chinor's INN from data.json: 203595219)
    print("\n--- Test 2: Lookup INN '203595219' ---")
    data = lookup_company_by_inn("203595219")
    if data:
        print(f"PASS: Found {data['name']}")
        print(f"Phone: {data.get('phone')}")
        if data.get('phone') == "93 101 55 78":
             print("PASS: Phone number matches known value")
        else:
             print(f"FAIL: Phone number mismatch. Expected '93 101 55 78', got '{data.get('phone')}'")
    else:
        print("FAIL: Lookup by INN failed")

if __name__ == "__main__":
    test_phone_extraction()
