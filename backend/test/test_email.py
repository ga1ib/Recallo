#!/usr/bin/env python3
"""
Test script for email functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_utils import send_exam_result_email, send_email

def test_basic_email():
    """Test basic email sending"""
    print("🧪 Testing basic email sending...")
    
    # Test with a simple email
    result = send_email(
        to="recallo.ai@gmail.com",  # Send to the same email for testing
        subject="🧪 Recallo Email Test",
        body="This is a test email from the Recallo notification system. If you receive this, the email system is working correctly!"
    )
    
    if result:
        print("✅ Basic email test PASSED")
    else:
        print("❌ Basic email test FAILED")
    
    return result

def test_quiz_result_email():
    """Test quiz result email"""
    print("🧪 Testing quiz result email...")
    
    # Test with different score ranges
    test_cases = [
        {"score": 9.5, "name": "High Scorer", "topic": "Advanced Mathematics"},
        {"score": 6.5, "name": "Average Learner", "topic": "Basic Science"},
        {"score": 3.0, "name": "Beginner Student", "topic": "Introduction to Programming"}
    ]
    
    results = []
    for case in test_cases:
        print(f"  Testing score {case['score']}/10...")
        result = send_exam_result_email(
            user_email="recallo.ai@gmail.com",
            user_name=case["name"],
            topic_title=case["topic"],
            score=case["score"]
        )
        results.append(result)
        
        if result:
            print(f"  ✅ Score {case['score']} test PASSED")
        else:
            print(f"  ❌ Score {case['score']} test FAILED")
    
    return all(results)

def main():
    """Run all email tests"""
    print("🚀 Starting Recallo Email System Tests")
    print("=" * 50)
    
    # Test 1: Basic email
    basic_result = test_basic_email()
    print()
    
    # Test 2: Quiz result emails
    quiz_result = test_quiz_result_email()
    print()
    
    # Summary
    print("📊 Test Results Summary:")
    print(f"  Basic Email: {'✅ PASS' if basic_result else '❌ FAIL'}")
    print(f"  Quiz Results: {'✅ PASS' if quiz_result else '❌ FAIL'}")
    
    if basic_result and quiz_result:
        print("\n🎉 All tests PASSED! Email system is working correctly.")
        return True
    else:
        print("\n❌ Some tests FAILED. Check email configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
