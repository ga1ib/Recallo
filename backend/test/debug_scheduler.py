#!/usr/bin/env python3
"""
Debug script for the notification scheduler system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_review_features_table():
    """Check if user_topic_review_features table exists and has data"""
    print("🔍 Checking user_topic_review_features table...")
    
    try:
        # Try to get the table structure first
        resp = supabase.table("user_topic_review_features").select("*").limit(1).execute()
        
        if resp.data:
            print("✅ Table exists and has data:")
            print(f"   Columns: {list(resp.data[0].keys())}")
            
            # Get all records
            all_resp = supabase.table("user_topic_review_features").select("*").execute()
            print(f"   Total records: {len(all_resp.data)}")
            
            for record in all_resp.data[:5]:  # Show first 5 records
                print(f"   📝 User: {record.get('user_id')}")
                print(f"      Topic: {record.get('topic_id')}")
                print(f"      Title: {record.get('title')}")
                print(f"      Score: {record.get('quiz_score')}")
                print(f"      Updated: {record.get('last_updated')}")
                print()
                
        else:
            print("⚠️ Table exists but is empty")
            
    except Exception as e:
        print(f"❌ Error accessing table: {e}")
        
        # Try to create the table
        print("🔧 Attempting to create table...")
        try:
            # This won't actually create the table, but will show if it exists
            supabase.table("user_topic_review_features").select("*").limit(0).execute()
            print("✅ Table exists but might have wrong structure")
        except Exception as e2:
            print(f"❌ Table doesn't exist: {e2}")

def check_notification_history():
    """Check notification history"""
    print("🔍 Checking user_notifications table...")
    
    try:
        resp = supabase.table("user_notifications").select("*").order("sent_at", desc=True).limit(10).execute()
        
        if resp.data:
            print(f"✅ Found {len(resp.data)} notification records:")
            for notif in resp.data:
                print(f"   📧 User: {notif.get('user_id')}")
                print(f"      Topic: {notif.get('topic_id')}")
                print(f"      Type: {notif.get('notification_type')}")
                print(f"      Sent: {notif.get('sent_at')}")
                print(f"      Date: {notif.get('sent_date')}")
                print()
        else:
            print("⚠️ No notification history found")
            
    except Exception as e:
        print(f"❌ Error accessing notifications table: {e}")

def check_recent_quiz_attempts():
    """Check recent quiz attempts that should trigger notifications"""
    print("🔍 Checking recent quiz attempts...")
    
    try:
        # Get recent attempts with scores < 8
        resp = supabase.table("quiz_attempts").select("user_id, topic_id, score, submitted_at").lt("score", 8).order("submitted_at", desc=True).limit(5).execute()
        
        if resp.data:
            print(f"✅ Found {len(resp.data)} recent attempts with score < 8:")
            for attempt in resp.data:
                user_id = attempt.get('user_id')
                topic_id = attempt.get('topic_id')
                score = attempt.get('score')
                submitted = attempt.get('submitted_at')
                
                print(f"   📝 User: {user_id}")
                print(f"      Topic: {topic_id}")
                print(f"      Score: {score}/10")
                print(f"      Submitted: {submitted}")
                
                # Check if this is in review_features
                try:
                    review_resp = supabase.table("user_topic_review_features").select("*").eq("user_id", user_id).eq("topic_id", topic_id).execute()
                    if review_resp.data:
                        print(f"      ✅ Found in review_features")
                    else:
                        print(f"      ❌ NOT in review_features - this is the problem!")
                except Exception as e:
                    print(f"      ❌ Error checking review_features: {e}")
                print()
        else:
            print("⚠️ No recent attempts with score < 8 found")
            
    except Exception as e:
        print(f"❌ Error checking quiz attempts: {e}")

def test_notification_functions():
    """Test the notification checking functions"""
    print("🔍 Testing notification functions...")
    
    # Import the functions from app.py
    try:
        from app import is_user_email_notification_enabled_global, is_daily_reminders_enabled, has_been_notified_today
        
        # Test with a known user
        test_user = "b9ddffb4-f3b8-45a3-aad7-d9153f786c71"
        test_topic = "865c6207-fe1c-442a-8504-9e860b9039fc"
        
        print(f"Testing with user: {test_user}")
        
        # Test global email notifications
        global_enabled = is_user_email_notification_enabled_global(test_user)
        print(f"   Global email notifications: {global_enabled}")
        
        # Test daily reminders
        daily_enabled = is_daily_reminders_enabled(test_user)
        print(f"   Daily reminders: {daily_enabled}")
        
        # Test if already notified today
        notified_today = has_been_notified_today(test_user, test_topic, "daily")
        print(f"   Already notified today: {notified_today}")
        
    except Exception as e:
        print(f"❌ Error testing functions: {e}")

def run_manual_notification_check():
    """Manually run the notification process"""
    print("🔍 Running manual notification check...")
    
    try:
        from app import process_notifications
        print("   Calling process_notifications()...")
        process_notifications()
        print("   ✅ Process completed")
        
    except Exception as e:
        print(f"❌ Error running notifications: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all debug checks"""
    print("🚀 Starting Notification Scheduler Debug")
    print("=" * 60)
    
    check_review_features_table()
    print()
    
    check_notification_history()
    print()
    
    check_recent_quiz_attempts()
    print()
    
    test_notification_functions()
    print()
    
    run_manual_notification_check()
    print()
    
    print("✅ Debug complete!")

if __name__ == "__main__":
    main()
