#!/usr/bin/env python3
"""
Simple test to add a record to review_features and test notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from matching_q_a import update_review_features
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_test_record():
    """Add a test record with score < 8 to trigger notifications"""
    print("🧪 Adding test record for notifications...")
    
    # Use existing user and a recent quiz attempt
    user_id = "b9ddffb4-f3b8-45a3-aad7-d9153f786c71"
    topic_id = "3c2787be-56c2-45db-a577-552d1de5a6db"  # From recent quiz attempts
    topic_title = "Test Notification Topic"
    score = 6.0  # Below 8, should trigger daily reminders
    
    print(f"👤 User: {user_id}")
    print(f"📚 Topic: {topic_id}")
    print(f"📊 Score: {score}/10 (should trigger daily reminders)")
    
    try:
        # Add the record
        update_review_features(user_id, topic_id, topic_title, score)
        
        # Verify it was added
        check_resp = supabase.table("user_topic_review_features") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("topic_id", topic_id) \
            .execute()
            
        if check_resp.data:
            record = check_resp.data[0]
            print("✅ Record successfully added:")
            print(f"   Title: {record.get('title')}")
            print(f"   Score: {record.get('quiz_score')}")
            print(f"   Mastered: {record.get('mastered')}")
            return True
        else:
            print("❌ Record not found after update")
            return False
            
    except Exception as e:
        print(f"❌ Error adding record: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler():
    """Test the notification scheduler"""
    print("🧪 Testing notification scheduler...")
    
    try:
        from app import process_notifications
        print("   Running process_notifications()...")
        process_notifications()
        print("   ✅ Scheduler completed")
        
        # Check if any notifications were sent
        notif_resp = supabase.table("user_notifications").select("*").order("sent_at", desc=True).limit(5).execute()
        
        if notif_resp.data:
            print(f"   📧 Found {len(notif_resp.data)} recent notifications:")
            for notif in notif_resp.data:
                print(f"      - {notif.get('notification_type')} to user {notif.get('user_id')}")
        else:
            print("   ⚠️ No notifications found in database")
            
        return True
        
    except Exception as e:
        print(f"❌ Error running scheduler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Testing Notification System")
    print("=" * 50)
    
    # Step 1: Add test record
    step1_success = add_test_record()
    print()
    
    if step1_success:
        # Step 2: Test scheduler
        step2_success = test_scheduler()
        print()
        
        if step2_success:
            print("🎉 Test completed!")
            print("📧 Check your email for notification!")
        else:
            print("❌ Scheduler test failed")
    else:
        print("❌ Failed to add test record")

if __name__ == "__main__":
    main()
