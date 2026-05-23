"""
PythonAnywhere Scheduled Task — POSTER
Runs once per hour. Posts if current hour matches schedule.
Set this as a scheduled task on PythonAnywhere to run every hour.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)

import anthropic
from datetime import datetime
from ig_brain.config import ANTHROPIC_KEY, POSTING_HOURS
from ig_brain.planner import generate_content_plan, generate_single_topic
from ig_brain.poster import run_poster
from ig_brain.memory import load_posted, load_memory

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
now    = datetime.now()

print(f"[POSTER] Running at {now.strftime('%Y-%m-%d %H:%M')} IST")

# Check if this is a posting hour
if now.hour not in POSTING_HOURS:
    print(f"[POSTER] Not a posting hour (schedule: {POSTING_HOURS}). Exiting.")
    sys.exit(0)

# Check if already posted this hour
posted = load_posted()
already = any(p.get("posted_at","")[:13] == now.strftime("%Y-%m-%dT%H") for p in posted)
if already:
    print(f"[POSTER] Already posted at hour {now.hour}. Exiting.")
    sys.exit(0)

# Load or generate content plan
PLAN_FILE = Path(__file__).parent / "content_plan.json"
import json

plan = []
if PLAN_FILE.exists():
    plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))

if not plan:
    print("[POSTER] Generating new content plan...")
    plan = generate_content_plan(client, days=7)
    PLAN_FILE.write_text(json.dumps(plan, indent=2, ensure_ascii="utf-8"), encoding="utf-8")

# Take next topic and post
topic_data = plan.pop(0)
PLAN_FILE.write_text(json.dumps(plan, indent=2), encoding="utf-8")

print(f"[POSTER] Posting: {topic_data.get('topic')}")
def decode_shortcode(code: str) -> str:
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    n = 0
    for c in code:
        n = n * 64 + alphabet.index(c)
    return str(n)

def save_to_posts_list(shortcode: str, caption: str = ""):
    pfile = Path(__file__).parent / "posts_list.json"
    posts = json.loads(pfile.read_text(encoding="utf-8")) if pfile.exists() else []
    codes = {p["code"] for p in posts}
    if shortcode not in codes:
        posts.insert(0, {"id": decode_shortcode(shortcode), "code": shortcode, "caption": caption[:80]})
        pfile.write_text(json.dumps(posts, indent=2), encoding="utf-8")
        print(f"[POSTER] posts_list.json updated ({len(posts)} posts)")

try:
    shortcode = run_poster(client, topic_data)
    save_to_posts_list(shortcode, topic_data.get("topic", ""))
    print(f"[POSTER] Success: https://www.instagram.com/p/{shortcode}/")
except Exception as e:
    print(f"[POSTER] Error: {e}")
    # Put topic back
    plan.insert(0, topic_data)
    PLAN_FILE.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    sys.exit(1)
