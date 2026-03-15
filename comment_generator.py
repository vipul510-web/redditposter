"""
Comment generation for the Reddit bot.
Supports template-based and LLM-based (OpenAI/Anthropic) contextual comments.
"""

import os
import random
from typing import Any

from config_loader import Config


def generate_comment_template(
    submission_title: str,
    submission_body: str,
    topic: dict[str, Any],
    config: Config,
) -> str:
    """
    Generate a comment using templates.
    Uses topic-specific templates if defined, otherwise fallback templates.
    Supports {insight} and {topic_specific_insight} placeholders for backwards compat.
    """
    templates = topic.get("templates") or config.comment_templates
    if not templates:
        templates = [
            "I've had a similar experience. {insight}",
            "Good question! {insight}",
        ]

    text = f"{submission_title} {submission_body}"[:500]
    keywords = topic.get("keywords", [])
    found = [kw for kw in keywords if kw.lower() in text.lower()]
    insight = f"Regarding {', '.join(found[:3])}" if found else topic.get("name", "this")

    template = random.choice(templates)
    # Support both placeholder names
    return template.replace("{insight}", insight).replace("{topic_specific_insight}", insight)


def generate_comment_openai(
    submission_title: str,
    submission_body: str,
    topic: dict[str, Any],
    config: Config,
) -> str:
    """Generate a contextual comment using OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Install openai: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    client = OpenAI(api_key=api_key)
    guidance = topic.get("comment_guidance", "Be helpful, concise, and genuine.")
    topic_name = topic.get("name", "the topic")

    prompt = f"""You are a helpful Reddit user. Write a SHORT, contextual comment (2-4 sentences max) in response to this post.

Topic: {topic_name}
Guidance: {guidance}

Post title: {submission_title}
Post body: {submission_body[:800]}

Rules:
- Be genuinely helpful, not promotional or spammy
- Sound like a real person, not a bot
- Do NOT start with "As an AI" or similar
- Keep it under 200 words
- Add value - don't just agree or say "great post"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_comment_anthropic(
    submission_title: str,
    submission_body: str,
    topic: dict[str, Any],
    config: Config,
) -> str:
    """Generate a contextual comment using Anthropic Claude API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError("Install anthropic: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    client = Anthropic(api_key=api_key)
    guidance = topic.get("comment_guidance", "Be helpful, concise, and genuine.")
    topic_name = topic.get("name", "the topic")

    prompt = f"""You are a helpful Reddit user. Write a SHORT, contextual comment (2-4 sentences max) in response to this post.

Topic: {topic_name}
Guidance: {guidance}

Post title: {submission_title}
Post body: {submission_body[:800]}

Rules:
- Be genuinely helpful, not promotional or spammy
- Sound like a real person, not a bot
- Do NOT start with "As an AI" or similar
- Keep it under 200 words
- Add value - don't just agree or say "great post"
"""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_comment(
    submission_title: str,
    submission_body: str,
    topic: dict[str, Any],
    config: Config,
) -> str:
    """
    Generate a contextual comment based on config.comment_mode.
    """
    mode = config.comment_mode.lower()

    if mode == "template":
        return generate_comment_template(
            submission_title, submission_body, topic, config
        )
    elif mode == "openai":
        return generate_comment_openai(
            submission_title, submission_body, topic, config
        )
    elif mode == "anthropic":
        return generate_comment_anthropic(
            submission_title, submission_body, topic, config
        )
    else:
        # Default to template
        return generate_comment_template(
            submission_title, submission_body, topic, config
        )
