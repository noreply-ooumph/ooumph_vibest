"""
GitHub Actions replier loop.
Runs 5 checks × 1 minute apart = effectively 1-minute reply time
within GitHub's 5-minute minimum cron window.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import anthropic
import requests
import random
import json

from ig_brain.config import ANTHROPIC_KEY, ACCOUNT_USERNAME, ACCOUNT_USER_ID, REPLY_SLEEP_MIN, REPLY_SLEEP_MAX, REPLIED_FILE
from ig_brain.replier import (
    load_replied, save_replied, load_web_session,
    fetch_posts, fetch_comments, generate_reply, post_reply
)

POSTS_LIST_FILE = Path(__file__).parent / "posts_list.json"

def load_posts_from_file() -> list:
    """Load posts from local posts_list.json (avoids Instagram API on cloud IPs)."""
    if POSTS_LIST_FILE.exists():
        import json as _j
        posts = _j.loads(POSTS_LIST_FILE.read_text(encoding="utf-8"))
        print(f"  Loaded {len(posts)} posts from posts_list.json")
        return posts
    return []

def decode_shortcode(code: str) -> str:
    """Decode Instagram shortcode to numeric media ID."""
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    n = 0
    for c in code:
        n = n * 64 + alphabet.index(c)
    return str(n)

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

CHECKS    = 5      # number of checks per run
INTERVAL  = 60     # seconds between checks (1 minute)

print(f"[REPLIER] Starting loop: {CHECKS} checks × {INTERVAL}s = {CHECKS} min window")

for check_num in range(1, CHECKS + 1):
    print(f"\n--- Check {check_num}/{CHECKS} ---")
    replied = load_replied()

    try:
        session  = load_web_session()
        # Use local posts_list.json to avoid Instagram API blocks on cloud IPs
        posts = load_posts_from_file()
        if not posts:
            # Fallback to API (works locally, may fail on cloud)
            try:
                posts = fetch_posts(session)
            except Exception as fe:
                print(f"  fetch_posts failed: {fe}")
                posts = []
        print(f"  Posts: {len(posts)} | Already replied: {len(replied)}")
        new_total = 0

        for post in posts:
            comments = fetch_comments(post["code"], session)
            new      = [c for c in comments if str(c["id"]) not in replied and c["text"].strip()]

            for c in new:
                print(f"  @{c['username']}: {c['text'][:60]}")
                try:
                    reply = generate_reply(client, c["text"], post["caption"])
                    print(f"  Reply: {reply}")
                    ok = post_reply(session, post["id"], c["id"], reply)
                    if ok:
                        replied.add(str(c["id"]))
                        save_replied(replied)
                        new_total += 1
                        print(f"  Replied OK.")
                    time.sleep(random.randint(REPLY_SLEEP_MIN, REPLY_SLEEP_MAX))
                except Exception as e:
                    print(f"  Error: {e}")
                    time.sleep(10)

        print(f"  Done. Replied to {new_total} new comments this check.")

    except Exception as e:
        print(f"  Check error: {e}")

    # Wait 1 minute before next check (skip wait on last loop)
    if check_num < CHECKS:
        print(f"  Waiting {INTERVAL}s...")
        time.sleep(INTERVAL)

print(f"\n[REPLIER] Loop complete.")
