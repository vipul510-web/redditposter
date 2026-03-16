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

    # Validate: need client_id, client_secret, and EITHER refresh_token (web app) OR username+password (script app)
    missing = []
    if not os.environ.get("REDDIT_CLIENT_ID"):
        missing.append("REDDIT_CLIENT_ID")
    if not os.environ.get("REDDIT_CLIENT_SECRET"):
        missing.append("REDDIT_CLIENT_SECRET")
    has_refresh = os.environ.get("REDDIT_REFRESH_TOKEN")
    has_creds = os.environ.get("REDDIT_USERNAME") and os.environ.get("REDDIT_PASSWORD")
    if not has_refresh and not has_creds:
        missing.append("REDDIT_REFRESH_TOKEN (web app) OR REDDIT_USERNAME + REDDIT_PASSWORD (script app)")
    if missing:
        print("Error: Missing:", ", ".join(missing))
        print("For web app: run 'python obtain_refresh_token.py' once to get REDDIT_REFRESH_TOKEN")
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
