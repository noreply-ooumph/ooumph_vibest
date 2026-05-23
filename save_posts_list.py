"""
Run this locally to save your current posts to posts_list.json.
GitHub Actions replier reads from this file instead of calling Instagram API.

Also appends new posts - safe to re-run anytime.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)


def decode_shortcode(code: str) -> str:
    """Decode Instagram shortcode to numeric media ID."""
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    n = 0
    for c in code:
        n = n * 64 + alphabet.index(c)
    return str(n)


def add_posts(new_posts: list, out_file: Path):
    """Merge new posts into posts_list.json, deduplicating by code."""
    existing = []
    if out_file.exists():
        existing = json.loads(out_file.read_text(encoding="utf-8"))
    existing_codes = {p["code"] for p in existing}
    added = 0
    for p in new_posts:
        if p["code"] not in existing_codes:
            # Ensure numeric ID is present
            if not p.get("id"):
                p["id"] = decode_shortcode(p["code"])
            existing.append(p)
            existing_codes.add(p["code"])
            added += 1
    out_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return existing, added


# ── Try fetching from Instagram API (works locally) ──────────────────────────
out = Path(__file__).parent / "posts_list.json"
fetched = []

try:
    from ig_brain.replier import load_web_session, fetch_posts
    session = load_web_session()
    fetched = fetch_posts(session)
    print(f"Fetched {len(fetched)} posts from Instagram API")
except Exception as e:
    print(f"API fetch failed ({e}), using existing list only")

if fetched:
    all_posts, added = add_posts(fetched, out)
    print(f"Added {added} new posts. Total: {len(all_posts)}")
else:
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8"))
        print(f"posts_list.json already has {len(existing)} posts (no changes)")
    else:
        print("No posts fetched and no existing posts_list.json found.")
        print("Run this script locally after IG session is active.")

# Print current list
if out.exists():
    posts = json.loads(out.read_text(encoding="utf-8"))
    for p in posts:
        print(f"  {p['code']}  id={p['id']}  {p.get('caption','')[:50]}")
