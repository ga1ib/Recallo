#!/usr/bin/env python3
"""
Notification Scheduler for Recallo
This script should be run daily (e.g., via cron job) to send reminder emails
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the notification processing function
from app import process_notifications

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_daily_notifications():
    """Run the daily notification process"""
    try:
        logging.info("🔄 Starting daily notification process...")
        process_notifications()
        logging.info("✅ Daily notification process completed successfully")
    except Exception as e:
        logging.error(f"❌ Error in daily notification process: {e}")
        import traceback
        traceback.print_exc()

def run_scheduler():
    """Run the scheduler that processes notifications daily"""
    logging.info("🚀 Starting Recallo Notification Scheduler")
    
    # Schedule daily notifications at 9:00 AM
    schedule.every().day.at("09:00").do(run_daily_notifications)
    
    # Also schedule at 6:00 PM for users in different timezones
    schedule.every().day.at("18:00").do(run_daily_notifications)
    
    logging.info("📅 Scheduled daily notifications at 9:00 AM and 6:00 PM")
    
    # Run once immediately for testing
    logging.info("🧪 Running initial notification check...")
    run_daily_notifications()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def run_once():
    """Run notifications once (for manual execution or cron jobs)"""
    logging.info("🔄 Running notification process once...")
    run_daily_notifications()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Recallo Notification Scheduler')
    parser.add_argument('--once', action='store_true', 
                       help='Run notifications once and exit (for cron jobs)')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as a daemon with scheduled intervals')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    elif args.daemon:
        run_scheduler()
    else:
        # Default: run once
        run_once()
