#!/usr/bin/env python3
"""
Debug script to check user email configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_user_data():
    """Check user data in the database"""
    print("🔍 Checking user data in database...")

    # First, try to get all columns to see the structure
    try:
        users_resp = supabase.table("users").select("*").limit(1).execute()

        if users_resp.data:
            print(f"📊 Users table structure:")
            for key in users_resp.data[0].keys():
                print(f"  📋 Column: {key}")
            print()

            # Now try different possible column names
            possible_selects = [
                "user_id, email, name",
                "id, email, name",
                "*"
            ]

            for select_str in possible_selects:
                try:
                    print(f"🔍 Trying select: {select_str}")
                    users_resp = supabase.table("users").select(select_str).limit(3).execute()

                    if users_resp.data:
                        print(f"✅ Success with {select_str}:")
                        for user in users_resp.data:
                            print(f"  👤 User: {user}")
                        break
                except Exception as e:
                    print(f"❌ Failed with {select_str}: {e}")

        else:
            print("❌ No users found in database")

    except Exception as e:
        print(f"❌ Error fetching users table: {e}")

        # Try to see if the table exists at all
        try:
            print("🔍 Checking if users table exists...")
            tables_resp = supabase.table("users").select("*").limit(0).execute()
            print("✅ Users table exists but might be empty")
        except Exception as e2:
            print(f"❌ Users table might not exist: {e2}")

def check_quiz_attempts():
    """Check recent quiz attempts"""
    print("🔍 Checking recent quiz attempts...")
    
    try:
        attempts_resp = supabase.table("quiz_attempts").select("user_id, topic_id, score, submitted_at").order("submitted_at", desc=True).limit(5).execute()
        
        if attempts_resp.data:
            print(f"📊 Found {len(attempts_resp.data)} recent attempts:")
            for attempt in attempts_resp.data:
                print(f"  📝 User ID: {attempt.get('user_id')}")
                print(f"     Topic ID: {attempt.get('topic_id')}")
                print(f"     Score: {attempt.get('score')}")
                print(f"     Submitted: {attempt.get('submitted_at')}")
                print()
        else:
            print("❌ No quiz attempts found")
            
    except Exception as e:
        print(f"❌ Error fetching quiz attempts: {e}")

def check_topics():
    """Check topics in database"""
    print("🔍 Checking topics...")
    
    try:
        topics_resp = supabase.table("topics").select("topic_id, title, user_id").limit(5).execute()
        
        if topics_resp.data:
            print(f"📊 Found {len(topics_resp.data)} topics:")
            for topic in topics_resp.data:
                print(f"  📚 Topic ID: {topic.get('topic_id')}")
                print(f"     Title: {topic.get('title')}")
                print(f"     User ID: {topic.get('user_id')}")
                print()
        else:
            print("❌ No topics found")
            
    except Exception as e:
        print(f"❌ Error fetching topics: {e}")

def test_user_email_lookup(user_id):
    """Test email lookup for a specific user"""
    print(f"🔍 Testing email lookup for user: {user_id}")

    try:
        user_resp = supabase.table("users").select("email, name").eq("user_id", user_id).single().execute()

        if user_resp.data:
            email = user_resp.data.get("email")
            name = user_resp.data.get("name", "Learner")
            print(f"  ✅ Found user:")
            print(f"     Email: {email}")
            print(f"     Name: {name}")

            if email:
                print(f"  📧 Email is configured - notifications should work")
                return True
            else:
                print(f"  ❌ No email configured - notifications will not work")
                return False
        else:
            print(f"  ❌ User not found")
            return False

    except Exception as e:
        print(f"  ❌ Error looking up user: {e}")
        return False

def main():
    """Run all debug checks"""
    print("🚀 Starting Recallo Email Debug")
    print("=" * 50)
    
    # Check user data
    check_user_data()
    print()
    
    # Check quiz attempts
    check_quiz_attempts()
    print()
    
    # Check topics
    check_topics()
    print()
    
    # Test specific users
    test_users = [
        "b9ddffb4-f3b8-45a3-aad7-d9153f786c71",  # Default user from frontend
        "8831479e-26a9-4021-9cb5-5fea202d0996",  # User with recent quiz attempts
        "f9a6bcaf-cac2-409e-8621-16e07be3f049"   # Another user with quiz attempts
    ]

    for user_id in test_users:
        print(f"🔍 Testing user ID: {user_id}")
        test_user_email_lookup(user_id)
        print()
    
    print("✅ Debug complete!")

if __name__ == "__main__":
    main()
