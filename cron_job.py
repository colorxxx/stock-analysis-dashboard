#!/usr/bin/env python3
"""
Railway Cron Job Service
Run this as a separate Railway service with cron schedule
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime

def run_daily_update():
    """Run the daily update script"""
    print("="*80)
    print(f"🕐 Starting scheduled update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        result = subprocess.run(
            ['python3', 'daily_update.py'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("✅ Update completed successfully")
        else:
            print(f"❌ Update failed with return code {result.returncode}")

    except subprocess.TimeoutExpired:
        print("❌ Update timed out after 10 minutes")
    except Exception as e:
        print(f"❌ Error running update: {str(e)}")

    print("="*80)

def main():
    """Main function to run scheduled tasks"""
    print("🚀 Railway Cron Job Service Started")
    print(f"📅 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⏰ Schedule: Daily at 22:00 UTC (after US market close)")
    print("="*80)

    # Run immediately on startup (optional)
    print("\n🔄 Running initial update...")
    run_daily_update()

    # Schedule daily at 22:00 UTC
    schedule.every().day.at("22:00").do(run_daily_update)

    print("\n⏳ Waiting for scheduled time...")

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
