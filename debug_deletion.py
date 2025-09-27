#!/usr/bin/env python3
"""
Debug script for account deletion.
"""

import requests
import sys

def test_deletion():
    """Test account deletion and show detailed error."""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Account Deletion Form Submission")
    print("=" * 50)
    
    # Test form submission
    form_data = {
        "email": "chris.charles.jones@gmail.com",
        "reason": "testing",
        "additional_info": "Debug test",
        "confirm_deletion": "on"
    }
    
    try:
        print(f"Submitting form data: {form_data}")
        response = requests.post(f"{base_url}/account-deletion", data=form_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Check if it's an error or success
            if "An unexpected error occurred" in response.text:
                print("❌ Error found in response")
                # Extract the error message
                import re
                error_match = re.search(r'An unexpected error occurred: ([^<]+)', response.text)
                if error_match:
                    print(f"Error details: {error_match.group(1)}")
                else:
                    print("Could not extract error details from HTML")
            elif "Confirmation Email Sent" in response.text:
                print("✅ Success! Confirmation email sent")
            else:
                print("⚠️ Unexpected response")
                print("Response preview:", response.text[:500])
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print("Response:", response.text[:500])
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_deletion()
