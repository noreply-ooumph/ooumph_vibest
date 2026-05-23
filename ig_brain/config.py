"""
Central config for vibestore.ooumph Instagram Brain
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# Account
ACCOUNT_USERNAME = "vibestore.ooumph"
ACCOUNT_USER_ID  = 62914966683
ACCOUNT_NICHE    = "trendy lifestyle products, fashion, home decor, gadgets, curated vibes"

# Posting schedule (24h IST hours to post)
POSTING_HOURS    = [9, 13, 18, 21]
POSTS_PER_DAY    = 2

# Comment reply settings
REPLY_CHECK_INTERVAL = 300
REPLY_SLEEP_MIN      = 20
REPLY_SLEEP_MAX      = 50

# Evolution
EVOLUTION_AFTER_POSTS = 5

# Paths
BASE_DIR      = Path(__file__).parent.parent
MEMORY_FILE   = BASE_DIR / "brain_memory.json"
POSTED_FILE   = BASE_DIR / "posted_content.json"
REPLIED_FILE  = BASE_DIR / "replied_comments.json"
IMAGES_DIR    = BASE_DIR / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)

# API Keys
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")

# Content pillars — vibestore lifestyle & product focus
CONTENT_PILLARS = [
    "Trending products you didn't know you needed",
    "Aesthetic home decor & interior vibes",
    "Fashion finds and style inspo",
    "Cool gadgets and tech accessories",
    "Budget-friendly lifestyle upgrades",
    "Minimal living and clean aesthetics",
    "Streetwear and casual fashion looks",
    "Gift ideas and curated collections",
    "Self-care and wellness products",
    "Unboxing and product discovery content",
]

HASHTAG_POOLS = {
    "lifestyle":    ["#lifestyle", "#vibes", "#aesthetic", "#livingmybestlife", "#dailyvibes", "#goodvibes", "#lifegoals"],
    "fashion":      ["#fashion", "#style", "#ootd", "#outfitinspo", "#streetwear", "#fashionblogger", "#trendy", "#fits"],
    "homedecor":    ["#homedecor", "#interiordesign", "#roomdecor", "#homeaesthetic", "#cozyvibes", "#minimal", "#homeliving"],
    "gadgets":      ["#gadgets", "#techlife", "#cooltech", "#techtok", "#gadgetlover", "#techfinds", "#innovation"],
    "shopping":     ["#shopping", "#onlineshopping", "#findsofinstagram", "#productreview", "#musthave", "#shopsmall"],
    "products":     ["#productphotography", "#newproduct", "#newcollection", "#limitededition", "#vibestore", "#ooumph"],
    "general":      ["#reels", "#explore", "#viral", "#trending", "#instareels", "#instagram", "#fyp"],
}
