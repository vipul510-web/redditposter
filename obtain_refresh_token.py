#!/usr/bin/env python3
"""
One-time setup: Get a Reddit refresh token for your web app.

Run this once to authorize your Reddit account. It will:
1. Open a URL in your browser
2. You click "Allow" on Reddit
3. You get a refresh token to add to .env

Requirements:
- Web app created at https://www.reddit.com/prefs/apps/
- Redirect URI must match EXACTLY: http://localhost:8080 (no trailing slash)
- REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env

Usage:
    python obtain_refresh_token.py
"""

import os
import random
import socket
import sys
from urllib.parse import parse_qs, urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import praw


def send_error(client, message):
    print(f"\nError: {message}")
    client.send(f"HTTP/1.1 200 OK\r\n\r\n{message}".encode())
    client.close()


def main():
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Error: Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
        sys.exit(1)

    # Redirect URI must match EXACTLY what's in your Reddit app settings
    redirect_uri = os.environ.get("REDDIT_REDIRECT_URI", "http://localhost:8080")

    scopes = ["read", "submit", "identity"]

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        user_agent="redditcommentor/1.0",
    )
    state = str(random.randint(0, 65000))
    url = reddit.auth.url(duration="permanent", scopes=scopes, state=state)

    print("\nIMPORTANT: Your Reddit app redirect URI must be EXACTLY:")
    print(f"   {redirect_uri}")
    print("   (Check at https://www.reddit.com/prefs/apps/ - edit your app)\n")
    print("1. Open this URL in your browser:")
    print(f"   {url}")
    print("\n2. Click 'Allow' to authorize the app")
    print("3. You'll be redirected to localhost - that's expected\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8080))
    server.listen(1)
    print("Waiting for redirect (do not close this window)...")
    client, _ = server.accept()
    server.close()

    data = client.recv(4096).decode("utf-8", errors="ignore")
    # Parse HTTP request - get the path (e.g. "/?code=xxx&state=yyy")
    try:
        first_line = data.split("\r\n", 1)[0]
        path = first_line.split(" ", 2)[1]
    except IndexError:
        send_error(client, "Could not parse request. Try again.")
        sys.exit(1)

    # Extract query params from path
    parsed = urlparse(path)
    params = parse_qs(parsed.query)
    params = {k: v[0] if v else "" for k, v in params.items()}

    if not params.get("code") and not params.get("error"):
        send_error(
            client,
            "No auth data received. If you saw 'invalid redirect_uri' on Reddit, "
            "edit your app at reddit.com/prefs/apps and set redirect URI to exactly: "
            "http://localhost:8080 (no trailing slash)",
        )
        sys.exit(1)

    if state != params.get("state"):
        send_error(client, "State mismatch. Try again.")
        sys.exit(1)
    if "error" in params:
        send_error(client, f"Reddit error: {params['error']}")
        sys.exit(1)

    refresh_token = reddit.auth.authorize(params["code"])
    client.send(
        f"HTTP/1.1 200 OK\r\n\r\nSuccess! Add this to your .env:\nREDDIT_REFRESH_TOKEN={refresh_token}".encode()
    )
    client.close()

    print("\n" + "=" * 60)
    print("Add this line to your .env file:")
    print(f"REDDIT_REFRESH_TOKEN={refresh_token}")
    print("=" * 60)
    print("\nYou can now remove REDDIT_USERNAME and REDDIT_PASSWORD from .env")


if __name__ == "__main__":
    main()
