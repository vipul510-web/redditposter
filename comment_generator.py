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
    matched_phrase: str | None = None,
) -> str | None:
    """
    OpenAI decides if the post fits our product; if yes, writes a human, contextual comment.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Install openai: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    client = OpenAI(api_key=api_key)
    app = config.product or {}
    app_name = app.get("name", "")
    app_desc = app.get("description", "")
    app_url = app.get("url", "")

    match_line = ""
    if matched_phrase:
        match_line = f'The post matched our monitor phrase: "{matched_phrase}" (still verify fit below).\n'

    prompt = f"""You are a helpful Reddit user. Your task has TWO parts.

{match_line}
PART 1 — FIT CHECK: Read the full post. Should someone from our side comment in a way that helps the OP?

We offer: "{app_name}" — {app_url} — {app_desc}

Comment ONLY if the post is genuinely about something we can help with, for example:
- WhatsApp Business API, webhooks, sending messages from code (Node, Python, etc.)
- Twilio WhatsApp, cost, or "too expensive" / alternatives
- Wati, Aisensy, or similar tool alternatives or pricing
- WhatsApp + dev tools (Cursor, Lovable, MCP, Claude Code, Codex) when the question ties to WhatsApp integration or messaging
- Lead capture, forms, surveys, drip campaigns over WhatsApp
- Setting up or costing WhatsApp Business API

Do NOT comment if:
- The post is only loosely related (e.g. generic Cursor/Lovable/SaaS chat with no WhatsApp/messaging angle)
- It is a job ad, meme, unrelated rant, or anything where a product mention would feel spammy
- You are not confident we add real value

If NO → respond with exactly: SKIP
If YES → go to Part 2.

PART 2 — COMMENT (only if YES):
1. Understand the specific question or problem in the post.
2. Write a short, useful reply (2–5 sentences) that directly helps — concrete, not generic.
3. Sound human: casual tone, contractions, no marketing speak.
4. Mention "{app_name}" or {app_url} only if it fits naturally (e.g. "we've been using…" or "something like Gavi might help with webhooks"). If it would feel forced, skip the plug and just help — but then prefer SKIP in Part 1 if there's nothing useful to say.
5. You may end with: "Happy to chat over DM if useful."
6. Under 180 words. Never start with "As an AI". No "Comment:" prefix.

Post title: {submission_title}
Post body: {submission_body[:1200]}

Output ONLY SKIP or the comment text — nothing else."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=280,
        temperature=0.55,
    )
    text = response.choices[0].message.content.strip()

    first = text.split("\n")[0].strip().upper().rstrip(".")
    if first == "SKIP":
        return None

    for prefix in ("Comment:", "Comment：", "comment:", "Comment: "):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip()
            break

    return text
