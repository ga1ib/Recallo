#!/usr/bin/env python3
"""
Test script to simulate quiz submission and email sending
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from matching_q_a import evaluate_and_save_quiz
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bhrwvazkvsebdxstdcow.supabase.co/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_quiz_submission_email():
    """Test email sending during quiz submission"""
    print("🧪 Testing quiz submission email...")

    # Find a topic that has questions
    try:
        # Get topics with questions
        questions_resp = supabase.table("quiz_questions").select("concept_id").limit(10).execute()

        if not questions_resp.data:
            print("❌ No questions found in database")
            return False

        # Get the first topic that has questions
        topic_id = questions_resp.data[0]["concept_id"]

        # Find a user who has taken quizzes
        attempts_resp = supabase.table("quiz_attempts").select("user_id").eq("topic_id", topic_id).limit(1).execute()

        # Use a user we know exists from our debug output
        user_id = "b9ddffb4-f3b8-45a3-aad7-d9153f786c71"  # Wahidul Islam Ziad
        print(f"🔍 Using known user: {user_id}")

        print(f"👤 User: {user_id}")
        print(f"📚 Topic: {topic_id}")

        # Get questions for this topic
        questions_resp = supabase.table("quiz_questions").select("question_id").eq("concept_id", topic_id).limit(3).execute()

        if not questions_resp.data:
            print("❌ No questions found for this topic")
            return False
            
        # Create fake quiz answers
        submitted_answers = []
        for i, question in enumerate(questions_resp.data):
            submitted_answers.append({
                "question_id": question["question_id"],
                "selected_answer": "A"  # Just pick A for all answers
            })
        
        print(f"📝 Submitting {len(submitted_answers)} answers...")
        
        # This should trigger the email sending
        result = evaluate_and_save_quiz(user_id, topic_id, submitted_answers)
        
        print(f"✅ Quiz submission result:")
        print(f"   Score: {result['score']}/10")
        print(f"   Correct: {result['correct_answers']}/{result['total_questions']}")
        
        print("📧 Check the email inbox for wahidul.islam.ziad@gmail.com")
        print("   If you received an email, the system is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during quiz submission: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Testing Quiz Email System")
    print("=" * 50)
    
    success = test_quiz_submission_email()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📧 Check your email inbox to confirm the email was sent.")
    else:
        print("\n❌ Test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
