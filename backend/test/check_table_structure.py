#!/usr/bin/env python3
"""
Check the exact table structure
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

def check_table_structure():
    """Check the exact structure and data types"""
    print("🔍 Checking user_topic_review_features table structure...")
    
    try:
        # Get a sample record to see the structure
        resp = supabase.table("user_topic_review_features").select("*").limit(1).execute()
        
        if resp.data:
            record = resp.data[0]
            print("📊 Sample record:")
            for key, value in record.items():
                print(f"   {key}: {value} (type: {type(value).__name__})")
            print()
            
            # Try to insert a minimal record to see what works
            print("🧪 Testing minimal insert...")
            test_data = {
                "user_id": "b9ddffb4-f3b8-45a3-aad7-d9153f786c71",
                "topic_id": "3c2787be-56c2-45db-a577-552d1de5a6db",
                "title": "Test Topic",
                "quiz_score": 6.0
            }
            
            try:
                insert_resp = supabase.table("user_topic_review_features").insert(test_data).execute()
                print("✅ Minimal insert successful")
                
                # Clean up the test record
                supabase.table("user_topic_review_features").delete().eq("user_id", test_data["user_id"]).eq("topic_id", test_data["topic_id"]).execute()
                
            except Exception as e:
                print(f"❌ Minimal insert failed: {e}")
                
                # Try with different data types
                print("🔧 Trying with integer boolean values...")
                test_data_int = {
                    "user_id": "b9ddffb4-f3b8-45a3-aad7-d9153f786c71",
                    "topic_id": "3c2787be-56c2-45db-a577-552d1de5a6db",
                    "title": "Test Topic",
                    "quiz_score": 6.0,
                    "mastered": 0,  # Try integer instead of boolean
                    "pass": 0,
                    "attempts_count": 1
                }
                
                try:
                    insert_resp = supabase.table("user_topic_review_features").insert(test_data_int).execute()
                    print("✅ Insert with integer booleans successful")
                    
                    # Clean up
                    supabase.table("user_topic_review_features").delete().eq("user_id", test_data_int["user_id"]).eq("topic_id", test_data_int["topic_id"]).execute()
                    
                except Exception as e2:
                    print(f"❌ Insert with integer booleans failed: {e2}")
        
    except Exception as e:
        print(f"❌ Error checking table: {e}")

if __name__ == "__main__":
    check_table_structure()
