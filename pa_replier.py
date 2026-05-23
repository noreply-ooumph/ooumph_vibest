"""
PythonAnywhere Scheduled Task — REPLIER
Runs every hour. Checks all posts for new comments and replies.
Set this as a scheduled task on PythonAnywhere to run every hour.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import time, random, requests, anthropic
from ig_brain.config import ANTHROPIC_KEY, ACCOUNT_USERNAME, ACCOUNT_USER_ID, REPLY_SLEEP_MIN, REPLY_SLEEP_MAX, REPLIED_FILE
from ig_brain.replier import (
    load_replied, save_replied, load_web_session,
    fetch_posts, fetch_comments, generate_reply, post_reply
)

client  = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
replied = load_replied()
print(f"[REPLIER] Starting. Already replied to {len(replied)} comments.")

try:
    session  = load_web_session()
    posts    = fetch_posts(session)
    print(f"[REPLIER] Checking {len(posts)} posts...")
    total    = 0

    for post in posts:
        comments = fetch_comments(post["id"], session)
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
                    total += 1
                    print(f"  Replied OK.")
                time.sleep(random.randint(REPLY_SLEEP_MIN, REPLY_SLEEP_MAX))
            except Exception as e:
                print(f"  Error: {e}")
                time.sleep(10)

    print(f"[REPLIER] Done. Replied to {total} new comments.")

except Exception as e:
    print(f"[REPLIER] Fatal error: {e}")
    sys.exit(1)
