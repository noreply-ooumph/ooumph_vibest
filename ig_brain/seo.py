"""
SEO + AEO Optimizer — captions, hashtags, image prompts via Claude.
"""
import random
from .config import HASHTAG_POOLS, CONTENT_PILLARS, ACCOUNT_NICHE
from .memory import load_memory


def pick_hashtags(topic: str, count: int = 25) -> list:
    t = topic.lower()
    pool = []
    if any(w in t for w in ["fashion","style","ootd","outfit","wear","cloth","streetwear","fit"]):
        pool += HASHTAG_POOLS.get("fashion", [])
    if any(w in t for w in ["home","decor","interior","room","aesthetic","cozy","minimal","living"]):
        pool += HASHTAG_POOLS.get("homedecor", [])
    if any(w in t for w in ["gadget","tech","cool","product","device","accessory","innovation"]):
        pool += HASHTAG_POOLS.get("gadgets", [])
    if any(w in t for w in ["shop","buy","find","gift","collection","limited","edition","unbox"]):
        pool += HASHTAG_POOLS.get("shopping", [])
    if any(w in t for w in ["lifestyle","vibe","aesthetic","self","wellness","care","upgrade"]):
        pool += HASHTAG_POOLS.get("lifestyle", [])
    pool += HASHTAG_POOLS.get("products", [])
    pool += HASHTAG_POOLS.get("general", [])
    seen, out = set(), []
    for tag in pool:
        if tag not in seen:
            seen.add(tag); out.append(tag)
    random.shuffle(out)
    return out[:count]


def generate_seo_caption(client, topic: str, pillar: str) -> str:
    mem      = load_memory()
    strategy = mem.get("strategy_notes", "")

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
        system=(
            "You are an expert Instagram SEO and AEO content writer for vibestore.ooumph, "
            f"a trendy lifestyle and product curation account. Niche: {ACCOUNT_NICHE}\n\n"
            "SEO Rules: First line = scroll-stopping lifestyle hook. Short punchy paragraphs.\n\n"
            "AEO Rules: Include a product insight or lifestyle fact early. "
            "Structure: Hook → Product/Lifestyle angle → Why it matters → CTA.\n\n"
            "Tone: cool curator — enthusiastic, trendy, aspirational but relatable. "
            "Format: 100-200 words. Fun emojis. End with 1 engaging question. NO hashtags."
        ),
        messages=[{"role": "user", "content": (
            f"Topic: {topic}\nPillar: {pillar}\nStrategy: {strategy}\n\nWrite the Instagram caption:"
        )}]
    )
    return resp.content[0].text.strip()


def generate_image_prompt(client, topic: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system="Write only a FLUX/Stable Diffusion image generation prompt. 2-3 sentences. No explanation.",
        messages=[{"role": "user", "content": (
            f"Topic: {topic}\n"
            "Style: clean product photography aesthetic, bright natural lighting, minimal background, "
            "trendy lifestyle vibes, Instagram-worthy, square 1:1 composition. No text in image."
        )}]
    )
    return resp.content[0].text.strip()
