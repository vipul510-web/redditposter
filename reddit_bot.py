"""
Reddit Comment Bot - Core logic for finding and posting contextual comments.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import praw
from praw.models import Submission

from config_loader import load_config, Config
from comment_generator import generate_comment


# State file to track which posts we've already commented on
STATE_FILE = Path(__file__).parent / "commented_posts.json"


def load_commented_posts() -> set[str]:
    """Load set of post IDs we've already commented on."""
    if not STATE_FILE.exists():
        return set()
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
            return set(data.get("post_ids", []))
    except (json.JSONDecodeError, IOError):
        return set()


def save_commented_post(post_id: str, config: Config):
    """Record that we commented on this post."""
    commented = load_commented_posts()
    commented.add(post_id)

    # Keep only recent entries to avoid unbounded growth (last 1000)
    commented_list = list(commented)
    if len(commented_list) > 1000:
        commented_list = commented_list[-1000:]

    with open(STATE_FILE, "w") as f:
        json.dump(
            {"post_ids": commented_list, "last_updated": datetime.now().isoformat()},
            f,
            indent=2,
        )


def create_reddit_client() -> praw.Reddit:
    """Create authenticated Reddit client from environment variables."""
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=f"redditcommentor:1.0 (by /u/{os.environ['REDDIT_USERNAME']})",
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
    )


def post_is_relevant(submission: Submission, config: Config) -> Optional[dict]:
    """
    Check if a post is relevant to our configured topics.
    Returns the matching topic dict if relevant, None otherwise.
    """
    text = f"{submission.title} {submission.selftext}".lower()

    for topic in config.topics:
        keywords = [k.lower() for k in topic["keywords"]]
        if any(kw in text for kw in keywords):
            return topic
    return None


def already_commented_on_reddit(submission: Submission, reddit: praw.Reddit) -> bool:
    """
    Check Reddit directly if we've already commented on this post.
    Used when state file isn't available (e.g. GitHub Actions) to avoid double-posting.
    """
    try:
        submission.comment_sort = "new"
        submission.comments.replace_more(limit=0)
        my_name = reddit.user.me().name
        for comment in submission.comments.list():
            if comment.author and comment.author.name == my_name:
                return True
    except Exception:
        pass
    return False


def post_passes_filters(submission: Submission, config: Config) -> bool:
    """Check if post passes quality/recency filters."""
    settings = config.settings

    if submission.score < settings.get("min_post_score", 0):
        return False

    post_time = datetime.fromtimestamp(submission.created_utc)
    max_age = timedelta(hours=settings.get("max_post_age_hours", 24))
    if datetime.now() - post_time > max_age:
        return False

    if submission.num_comments > settings.get("max_existing_comments", 100):
        return False

    min_karma = settings.get("min_author_karma", 0)
    if min_karma > 0 and submission.author:
        try:
            if submission.author.link_karma + submission.author.comment_karma < min_karma:
                return False
        except Exception:
            pass  # If we can't get karma, allow the post

    return True


def run_bot(dry_run: bool = False):
    """
    Main bot loop: find relevant posts and post contextual comments.
    Set dry_run=True to only print what would be done without posting.
    """
    config = load_config()
    reddit = create_reddit_client()

    commented_ids = load_commented_posts() if config.settings.get("skip_already_commented", True) else set()
    comments_posted = 0
    max_comments = config.settings.get("max_comments_per_run", 5)
    delay = config.settings.get("delay_between_comments", 300)

    print(f"Starting bot run (dry_run={dry_run})")
    print(f"Subreddits: {config.subreddits}")
    print(f"Max comments this run: {max_comments}")
    print("-" * 50)

    for subreddit_name in config.subreddits:
        if comments_posted >= max_comments:
            break

        try:
            subreddit = reddit.subreddit(subreddit_name)
            sort = config.settings.get("post_sort", "new")
            limit = config.settings.get("posts_per_subreddit", 25)

            # Get posts based on sort order
            if sort == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort == "new":
                posts = subreddit.new(limit=limit)
            elif sort == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                posts = subreddit.hot(limit=limit)

            for submission in posts:
                if comments_posted >= max_comments:
                    break

                # Skip if already commented
                if submission.id in commented_ids:
                    continue

                # Check filters
                if not post_passes_filters(submission, config):
                    continue

                # Check topic relevance
                topic = post_is_relevant(submission, config)
                if not topic:
                    continue

                # Generate comment
                try:
                    comment_text = generate_comment(
                        submission_title=submission.title,
                        submission_body=submission.selftext or "",
                        topic=topic,
                        config=config,
                    )
                except Exception as e:
                    print(f"  [ERROR] Failed to generate comment for {submission.id}: {e}")
                    continue

                if not comment_text or len(comment_text.strip()) < 10:
                    if comment_text is None:
                        print(f"  [SKIP] OpenAI assessed post as not relevant: {submission.title[:50]}...")
                    continue

                # Post or simulate
                if dry_run:
                    print(f"\n[DRY RUN] Would comment on: {submission.title[:60]}...")
                    print(f"  URL: https://reddit.com{submission.permalink}")
                    print(f"  Topic: {topic['name']}")
                    print(f"  Comment: {comment_text[:200]}...")
                else:
                    # Double-check we haven't already commented (important when state isn't persisted, e.g. GitHub Actions)
                    if already_commented_on_reddit(submission, reddit):
                        print(f"  [SKIP] Already commented on {submission.id}")
                        commented_ids.add(submission.id)
                        continue
                    try:
                        submission.reply(comment_text)
                        print(f"\n[POSTED] Commented on: {submission.title[:60]}...")
                        print(f"  URL: https://reddit.com{submission.permalink}")
                        save_commented_post(submission.id, config)
                        comments_posted += 1
                        time.sleep(delay)
                    except praw.exceptions.RedditAPIException as e:
                        print(f"  [ERROR] Reddit API: {e}")
                    except Exception as e:
                        print(f"  [ERROR] {e}")

        except Exception as e:
            print(f"[ERROR] Processing r/{subreddit_name}: {e}")

    print("-" * 50)
    print(f"Run complete. Comments posted: {comments_posted}")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    run_bot(dry_run=dry_run)
