"""
SEO + AEO Optimizer — captions, hashtags, image prompts via Claude.
"""
import random
from .config import HASHTAG_POOLS, CONTENT_PILLARS, ACCOUNT_NICHE
from .memory import load_memory


def pick_hashtags(topic: str, count: int = 25) -> list:
    t = topic.lower()
    pool = []
    if any(w in t for w in ["myth","mahab","ramay","vedic","hindu","epic","sacred","symbol","devotion"]):
        pool += HASHTAG_POOLS["mythology"]
    if any(w in t for w in ["history","ancient","nalanda","civiliz","war","king","empire","lost"]):
        pool += HASHTAG_POOLS["history"]
    if any(w in t for w in ["ai","artificial","generat","tech","future","digital"]):
        pool += HASHTAG_POOLS["ai"]
    if any(w in t for w in ["animal","hybrid","wildlife","nature","shark","horse"]):
        pool += HASHTAG_POOLS["animals"]
    if any(w in t for w in ["philosoph","wisdom","conscious","soul","spirit","meaning"]):
        pool += HASHTAG_POOLS["philosophy"]
    pool += HASHTAG_POOLS["storytelling"]
    pool += HASHTAG_POOLS["general"]
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
        model="claude-sonnet-4-5",
        max_tokens=600,
        system=(
            "You are an expert Instagram SEO and AEO content writer for story.matters_, "
            f"an AI storytelling account. Niche: {ACCOUNT_NICHE}\n\n"
            "SEO Rules: First line = powerful hook (shown in feed before 'more'). "
            "Include 2-3 natural keyword phrases. Short paragraphs.\n\n"
            "AEO Rules (for Google SGE, Perplexity, ChatGPT): Include a direct factual statement early. "
            "Structure: Hook → Facts → Story → Insight → CTA.\n\n"
            "Format: 150-250 words. Natural emojis. End with 1 engaging question. NO hashtags."
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
            "Style: cinematic, epic, dramatic lighting, dark atmosphere, hyper-detailed, "
            "AI art style, suitable for Instagram storytelling account. Square 1:1 composition. No text."
        )}]
    )
    return resp.content[0].text.strip()
