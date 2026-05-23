"""
GitHub Actions replier loop — uses instagrapi mobile API.
Runs 5 checks x 1 minute apart = 5 min window per run.
"""
import sys, os, time, json, random
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import anthropic
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

from ig_brain.config import ANTHROPIC_KEY, ACCOUNT_USERNAME, ACCOUNT_USER_ID, REPLY_SLEEP_MIN, REPLY_SLEEP_MAX, REPLIED_FILE
from ig_brain.replier import load_replied, save_replied

SETTINGS_FILE   = Path(__file__).parent / "ig_settings.json"
POSTS_LIST_FILE = Path(__file__).parent / "posts_list.json"

REPLY_SYSTEM = """You are the voice behind vibestore.ooumph, an Instagram page about trendy lifestyle products, fashion, home decor, gadgets, and curated vibes.

Reply to a comment on one of your posts. Rules:
- 1-2 sentences max
- Sound like a cool, knowledgeable curator — enthusiastic but not salesy
- If they asked about a product or where to buy, be helpful and invite them to DM or explore
- If praise, be warm and authentic
- If a question about a product or style, give a crisp helpful answer
- Emojis are welcome — keep it trendy and fun
- Never start with "Thanks for commenting!" or "Glad you liked it!"
- Vary sentence openers — don't always start with "We" or "I"
"""

def get_client() -> Client:
    cl = Client()
    cl.delay_range = [1, 3]
    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    if "_instagrapi" in settings:
        cl.set_settings(settings["_instagrapi"])
    cl.login(os.environ.get("IG_USERNAME", ACCOUNT_USERNAME),
             os.environ.get("IG_PASSWORD", ""))
    return cl

def load_posts() -> list:
    if POSTS_LIST_FILE.exists():
        posts = json.loads(POSTS_LIST_FILE.read_text(encoding="utf-8"))
        print(f"  Loaded {len(posts)} posts from posts_list.json")
        return posts
    return []

def generate_reply_text(client_ai, comment: str, caption: str) -> str:
    resp = client_ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=REPLY_SYSTEM,
        messages=[{"role": "user", "content": f"Post topic: {caption[:80]}\nComment: {comment}\n\nReply:"}]
    )
    return resp.content[0].text.strip().strip('"').strip("'")

client_ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
CHECKS = 5
INTERVAL = 60

print(f"[REPLIER] Starting: {CHECKS} checks x {INTERVAL}s")

try:
    cl = get_client()
    print(f"  Logged in as user_id={cl.user_id}")
except Exception as e:
    print(f"  Login failed: {e}")
    sys.exit(1)

for check_num in range(1, CHECKS + 1):
    print(f"\n--- Check {check_num}/{CHECKS} ---")
    replied = load_replied()
    posts   = load_posts()
    new_total = 0

    for post in posts:
        print(f"  Post {post['code']}...", end="")
        try:
            comments = cl.media_comments(post["id"], amount=50)
            fresh = []
            for c in comments:
                uid  = str(c.user.pk)
                text = c.text.strip()
                if uid == str(ACCOUNT_USER_ID):
                    continue
                if text.lower().startswith(f"@{ACCOUNT_USERNAME.lower()}"):
                    continue
                if str(c.pk) in replied:
                    continue
                if hasattr(c, 'child_comment_count') and c.child_comment_count > 0:
                    try:
                        children = cl.media_comment_replies(post["id"], str(c.pk))
                        if any(str(ch.user.pk) == str(ACCOUNT_USER_ID) for ch in children):
                            continue
                    except Exception:
                        pass
                fresh.append(c)
            print(f" {len(fresh)} new comments")

            for c in fresh:
                print(f"    @{c.user.username}: {c.text[:50]}")
                try:
                    reply_text = generate_reply_text(client_ai, c.text, post.get("caption", ""))
                    print(f"    Reply: {reply_text}")
                    cl.media_comment(post["id"], reply_text, replied_to_comment_id=str(c.pk))
                    replied.add(str(c.pk))
                    save_replied(replied)
                    new_total += 1
                    print(f"    Replied OK")
                    time.sleep(random.randint(REPLY_SLEEP_MIN, REPLY_SLEEP_MAX))
                except Exception as e:
                    print(f"    Reply error: {e}")
                    time.sleep(10)

        except (LoginRequired, ChallengeRequired) as e:
            print(f"\n  SESSION ERROR: {e}")
            break
        except Exception as e:
            print(f" error: {e}")

    print(f"  Done. Replied to {new_total} new comments this check.")
    if check_num < CHECKS:
        print(f"  Waiting {INTERVAL}s...")
        time.sleep(INTERVAL)

print(f"\n[REPLIER] Loop complete.")

# Save updated session so tokens stay fresh for next run
try:
    updated = {"_instagrapi": cl.get_settings(), "user_id": str(cl.user_id)}
    SETTINGS_FILE.write_text(json.dumps(updated, indent=2))
    print("[REPLIER] Session state saved.")
except Exception as e:
    print(f"[REPLIER] Warning: session save failed: {e}")
