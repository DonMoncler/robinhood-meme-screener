"""
Local entry point. Runs the poll cycle on a fixed interval. Only needed
if you want to run this on your own machine instead of / in addition to
the GitHub Actions workflow.
"""
import time
import schedule

from config import POLL_INTERVAL_MINUTES
from storage import init_db
from poller import run_cycle


def job():
    print("=" * 60)
    print("Running poll cycle...")
    run_cycle()


if __name__ == "__main__":
    init_db()
    job()
    schedule.every(POLL_INTERVAL_MINUTES).minutes.do(job)
    print(f"Scheduler started -- polling every {POLL_INTERVAL_MINUTES} min. Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)
