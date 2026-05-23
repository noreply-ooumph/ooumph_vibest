"""
Auto Comment Replier — monitors all posts, replies to every comment with Claude.
"""
import json, time, random, requests
from pathlib import Path
from .config import ACCOUNT_USERNAME, ACCOUNT_USER_ID, REPLY_SLEEP_MIN, REPLY_SLEEP_MAX, REPLIED_FILE

REPLY_SYSTEM = """You are the voice behind vibestore.ooumph, an Instagram store for trendy lifestyle products, fashion, home decor, and curated vibes.

Reply to a comment on one of your posts. Rules:
- 1-2 sentences max
- Sound like a cool, friendly store owner — not a corporate brand
- If they asked about a product, be helpful and enthusiastic
- If praise, be warm and genuine
- If a buying question, be encouraging and direct
- Emojis are welcome — keep it fun and on-brand
- Never start with "Thanks for shopping!" or "Glad you liked it!"
- Vary sentence openers — don't always start with "We" or "I"
"""


def load_replied() -> set:
    if REPLIED_FILE.exists():
        return set(json.loads(REPLIED_FILE.read_text(encoding="utf-8")))
    return set()

def save_replied(ids: set):
    REPLIED_FILE.write_text(json.dumps(list(ids), indent=2), encoding="utf-8")

def load_web_session() -> requests.Session:
    settings = json.loads((Path(__file__).parent.parent / "ig_settings.json").read_text(encoding="utf-8"))
    cookies  = settings.get("cookies", {})
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "X-CSRFToken": cookies.get("csrftoken", ""),
        "X-Instagram-AJAX": "1",
        "Referer": f"https://www.instagram.com/{ACCOUNT_USERNAME}/",
        "Origin": "https://www.instagram.com",
        "Accept": "application/json",
    })
    for k, v in cookies.items():
        s.cookies.set(k, v, domain=".instagram.com")
    return s

def fetch_posts(session: requests.Session = None) -> list:
    """Fetch posts — uses authenticated session if provided (needed on cloud IPs)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "x-ig-app-id": "936619743392459",
        "Accept": "application/json",
    }
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={ACCOUNT_USERNAME}"

    # Try with session cookies first (works on cloud IPs)
    if session:
        r = session.get(url, headers={**session.headers, **headers}, timeout=15)
    else:
        r = requests.get(url, headers=headers, timeout=15)

    if r.status_code != 200 or not r.content:
        raise ValueError(f"fetch_posts failed: status={r.status_code} len={len(r.content)}")

    data  = r.json()
    edges = data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
    return [
        {
            "id":      e["node"]["id"],
            "code":    e["node"]["shortcode"],
            "caption": (e["node"].get("edge_media_to_caption", {}).get("edges") or [{}])[0].get("node", {}).get("text", ""),
        }
        for e in edges
    ]

def fetch_comments(post_code: str, session: requests.Session) -> list:
    """Fetch comments via GraphQL — the only endpoint that works with web cookies."""
    try:
        import urllib.parse
        variables = json.dumps({"shortcode": post_code, "first": 50})
        url = (
            "https://www.instagram.com/graphql/query/"
            "?query_hash=bc3296d1ce80a24b1b6e40b1e72903f5"
            f"&variables={urllib.parse.quote(variables)}"
        )
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return []
        data  = r.json()
        edges = (data.get("data", {})
                     .get("shortcode_media", {})
                     .get("edge_media_to_parent_comment", {})
                     .get("edges", []))
        result = []
        for e in edges:
            node = e.get("node", {})
            owner = node.get("owner", {})
            uid   = str(owner.get("id", ""))
            text  = node.get("text", "").strip()
            # Skip own comments
            if uid == str(ACCOUNT_USER_ID):
                continue
            # Skip replies-to-replies: comments that @mention our account
            if text.lower().startswith(f"@{ACCOUNT_USERNAME.lower()}"):
                continue
            # Skip if we already replied (threaded replies contain our user_id)
            threaded = (node.get("edge_threaded_comments", {}).get("edges") or [])
            already_replied = any(
                str(r.get("node", {}).get("owner", {}).get("id", "")) == str(ACCOUNT_USER_ID)
                for r in threaded
            )
            if already_replied:
                continue
            result.append({
                "id":       str(node.get("id", "")),
                "text":     text,
                "username": owner.get("username", ""),
                "user_id":  uid,
            })
        return result
    except Exception as ex:
        print(f"  fetch_comments error: {ex}")
        return []

def generate_reply(client, comment: str, caption_hint: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=REPLY_SYSTEM,
        messages=[{"role": "user", "content": f"Post topic: {caption_hint[:80]}\nComment: {comment}\n\nReply:"}]
    )
    return resp.content[0].text.strip().strip('"').strip("'")

def post_reply(session: requests.Session, post_id: str, comment_id: str, text: str) -> bool:
    r = session.post(
        f"https://www.instagram.com/api/v1/web/comments/{post_id}/add/",
        data={"comment_text": text, "replied_to_comment_id": comment_id},
        headers={**session.headers, "Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    return r.status_code in (200, 201)


def run_replier(client, check_interval: int = 300):
    print(f"[REPLIER] Auto-reply started for @{ACCOUNT_USERNAME}")
    replied = load_replied()
    print(f"  {len(replied)} comments already replied to.\n")

    while True:
        try:
            session = load_web_session()
            posts   = fetch_posts(session)
            print(f"[{time.strftime('%H:%M:%S')}] Checking {len(posts)} posts for new comments...")
            new_replies = 0

            for post in posts:
                comments = fetch_comments(post["code"], session)
                new_comments = [c for c in comments if str(c["id"]) not in replied and c["text"].strip()]

                for c in new_comments:
                    print(f"\n  @{c['username']}: {c['text'][:60]}")
                    try:
                        reply = generate_reply(client, c["text"], post["caption"])
                        print(f"  Reply: {reply}")
                        ok = post_reply(session, post["id"], c["id"], reply)
                        if ok:
                            replied.add(str(c["id"]))
                            save_replied(replied)
                            new_replies += 1
                            print(f"  Replied OK.")
                        time.sleep(random.randint(REPLY_SLEEP_MIN, REPLY_SLEEP_MAX))
                    except Exception as e:
                        print(f"  Reply error: {e}")
                        time.sleep(20)

            if new_replies == 0:
                print(f"  No new comments. Next check in {check_interval//60} min.")

        except KeyboardInterrupt:
            print("\n[REPLIER] Stopped.")
            break
        except Exception as e:
            print(f"[REPLIER] Error: {e}")
            time.sleep(60)

        time.sleep(check_interval)
