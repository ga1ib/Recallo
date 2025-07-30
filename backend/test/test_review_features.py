#!/usr/bin/env python3
"""
Test the update_review_features function
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from matching_q_a import update_review_features
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_update_review_features():
    """Test updating review features"""
    print("🧪 Testing update_review_features function...")
    
    # Use test data
    user_id = "b9ddffb4-f3b8-45a3-aad7-d9153f786c71"
    topic_id = "test-topic-" + str(int(time.time()))  # Unique topic ID
    topic_title = "Test Topic for Notifications"
    score = 6.5  # Below 8, should trigger daily reminders
    
    print(f"👤 User: {user_id}")
    print(f"📚 Topic: {topic_id}")
    print(f"📊 Score: {score}/10")
    
    try:
        # Test the function
        update_review_features(user_id, topic_id, topic_title, score)
        
        # Verify it was added
        check_resp = supabase.table("user_topic_review_features") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("topic_id", topic_id) \
            .execute()
            
        if check_resp.data:
            record = check_resp.data[0]
            print("✅ Record successfully added/updated:")
            print(f"   Title: {record.get('title')}")
            print(f"   Score: {record.get('quiz_score')}")
            print(f"   Attempts: {record.get('attempts_count')}")
            print(f"   Mastered: {record.get('mastered')}")
            return True
        else:
            print("❌ Record not found after update")
            return False
            
    except Exception as e:
        print(f"❌ Error testing function: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_scheduler():
    """Test the notification scheduler"""
    print("🧪 Testing notification scheduler...")
    
    try:
        from app import process_notifications
        print("   Running process_notifications()...")
        process_notifications()
        print("   ✅ Scheduler completed")
        return True
        
    except Exception as e:
        print(f"❌ Error running scheduler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing Review Features and Notifications")
    print("=" * 50)
    
    import time
    
    # Test 1: Update review features
    test1_result = test_update_review_features()
    print()
    
    # Test 2: Run scheduler
    test2_result = test_notification_scheduler()
    print()
    
    if test1_result and test2_result:
        print("🎉 All tests passed!")
        print("📧 Check your email for notifications!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()
