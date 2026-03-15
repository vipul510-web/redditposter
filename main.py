#!/usr/bin/env python3
"""
Reddit Comment Bot - Automated contextual commenting on relevant posts.

Usage:
  python main.py              # Run the bot
  python main.py --dry-run     # Preview what would be commented (no posting)
  python main.py --once        # Single run (default)
  python main.py --loop 3600   # Run every hour (3600 seconds)

Set up:
  1. Copy .env.example to .env and fill in Reddit API credentials
  2. Edit config.yaml with your subreddits and topics
  3. Run with --dry-run first to verify
"""

import os
import sys
import time
import argparse

# Load .env before importing bot (which needs env vars)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional

from reddit_bot import run_bot


def main():
    parser = argparse.ArgumentParser(description="Reddit contextual comment bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without posting comments",
    )
    parser.add_argument(
        "--loop",
        type=int,
        metavar="SECONDS",
        help="Run continuously, waiting SECONDS between runs",
    )
    args = parser.parse_args()

    # Validate required env vars
    required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print("Error: Missing required environment variables:", ", ".join(missing))
        print("Copy .env.example to .env and fill in your Reddit API credentials.")
        sys.exit(1)

    if args.loop:
        print(f"Running in loop mode (interval: {args.loop}s). Ctrl+C to stop.")
        while True:
            try:
                run_bot(dry_run=args.dry_run)
            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except Exception as e:
                print(f"Run error: {e}")
            time.sleep(args.loop)
    else:
        run_bot(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
