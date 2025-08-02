#!/usr/bin/env python3
"""
Script to set up missing notification tables and populate with default settings
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_notification_settings_table():
    """Create user_notification_settings table if it doesn't exist"""
    print("🔧 Setting up user_notification_settings table...")
    
    # Get all unique user IDs from existing tables
    try:
        users_resp = supabase.table("users").select("user_id, email").execute()
        if not users_resp.data:
            print("❌ No users found in users table")
            return
        
        print(f"✅ Found {len(users_resp.data)} users")
        
        # Try to create default notification settings for each user
        for user in users_resp.data:
            user_id = user["user_id"]
            email = user["email"]
            
            try:
                # Check if settings already exist
                existing_resp = supabase.table("user_notification_settings") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .execute()
                
                if existing_resp.data and len(existing_resp.data) > 0:
                    print(f"   Settings already exist for {email}")
                    continue
                
                # Create default settings
                settings_data = {
                    "user_id": user_id,
                    "email_notifications_enabled": True,
                    "daily_reminders_enabled": True,
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                
                insert_resp = supabase.table("user_notification_settings") \
                    .insert(settings_data) \
                    .execute()
                
                if insert_resp.data:
                    print(f"   ✅ Created settings for {email}")
                else:
                    print(f"   ❌ Failed to create settings for {email}")
                    
            except Exception as e:
                print(f"   ❌ Error creating settings for {email}: {e}")
                
    except Exception as e:
        print(f"❌ Error setting up notification settings: {e}")

def create_topic_notification_preferences():
    """Create default topic notification preferences"""
    print("\n🔧 Setting up topic notification preferences...")
    
    try:
        # Get all user-topic combinations from user_topic_review_features
        review_resp = supabase.table("user_topic_review_features") \
            .select("user_id, topic_id") \
            .execute()
        
        if not review_resp.data:
            print("❌ No user-topic combinations found")
            return
        
        print(f"✅ Found {len(review_resp.data)} user-topic combinations")
        
        for record in review_resp.data:
            user_id = record["user_id"]
            topic_id = record["topic_id"]
            
            try:
                # Check if preference already exists
                existing_resp = supabase.table("user_topic_notification_preferences") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .eq("topic_id", topic_id) \
                    .execute()
                
                if existing_resp.data and len(existing_resp.data) > 0:
                    continue  # Already exists
                
                # Create default preference (enabled)
                pref_data = {
                    "user_id": user_id,
                    "topic_id": topic_id,
                    "enabled": True,
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                
                insert_resp = supabase.table("user_topic_notification_preferences") \
                    .insert(pref_data) \
                    .execute()
                
                if insert_resp.data:
                    print(f"   ✅ Created preference for {user_id[:8]}.../{topic_id[:8]}...")
                    
            except Exception as e:
                print(f"   ❌ Error creating preference for {user_id[:8]}.../{topic_id[:8]}...: {e}")
                
    except Exception as e:
        print(f"❌ Error setting up topic preferences: {e}")

def test_notification_system():
    """Test the notification system"""
    print("\n🧪 Testing notification system...")
    
    try:
        from routes.notifications import process_notifications
        process_notifications()
        print("✅ Notification system test completed")
    except Exception as e:
        print(f"❌ Error testing notification system: {e}")

if __name__ == "__main__":
    print("🚀 Setting up notification system...")
    
    create_notification_settings_table()
    create_topic_notification_preferences()
    test_notification_system()
    
    print("\n🎉 Notification system setup completed!")
