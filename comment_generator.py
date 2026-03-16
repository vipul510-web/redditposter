"""
Comment generation for the Reddit bot.
Uses OpenAI to assess post relevance and generate contextual comments.
"""

import os
from typing import Any

from config_loader import Config


def generate_comment(
    submission_title: str,
    submission_body: str,
    topic: dict[str, Any],
    config: Config,
) -> str | None:
    """
    Uses OpenAI to:
    1. Assess if the post is about AI visibility, ChatGPT, or AEO - if not, returns None (skip)
    2. If relevant, generates a helpful comment with subtle app hint and DM offer
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Install openai: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    client = OpenAI(api_key=api_key)
    app = config.shopify_app or {}
    app_name = app.get("name", "")
    app_desc = app.get("description", "")
    app_url = app.get("url", "")

    prompt = f"""You are a helpful Reddit user. Your task has TWO parts:

PART 1 - ASSESS: Is this post specifically asking about AI visibility, visibility on ChatGPT, AEO (Answer Engine Optimization), AI SEO, or ranking on AI platforms?

- If NO (e.g. American Eagle Outfitters work, schedules, unrelated topics) → respond with exactly: SKIP
- If YES (they're asking about AI/ChatGPT visibility, AEO, etc.) → proceed to Part 2

PART 2 - COMMENT: If relevant, you must:
1. UNDERSTAND the actual question or content in the post - read it carefully
2. FRAME a helpful answer that directly addresses what they asked - be specific, not generic
3. SOUND HUMAN - write like a real person sharing experience, not a bot or marketer. Use casual language, contractions, natural phrasing.
4. Optionally slide in our app when it naturally fits: "{app_name}" ({app_url}) - {app_desc}
   - Only mention it when it genuinely helps answer their question
   - Be subtle: "I've been using [app name] for this" or "something like [app] might help" - never pushy
   - If it doesn't fit, skip the mention and just give helpful insights
5. End with: "Happy to discuss more over DM if you'd like."
6. Under 150 words. No "As an AI" or similar.

Post title: {submission_title}
Post body: {submission_body[:1000]}

Respond with either SKIP or your comment. Nothing else."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.6,
    )
    text = response.choices[0].message.content.strip()

    if text.upper().strip() == "SKIP":
        return None
    return text
