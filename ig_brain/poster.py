"""
Auto Poster — generates image + SEO caption, posts to Instagram via web API.
"""
import json, time, random, requests
from pathlib import Path
from .config import ACCOUNT_USERNAME, IMAGES_DIR
from .seo import pick_hashtags, generate_seo_caption, generate_image_prompt
from .image_gen import generate_image_hf
from .memory import load_memory, record_post, load_posted, evolve_strategy
from .config import EVOLUTION_AFTER_POSTS


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
    })
    for k, v in cookies.items():
        s.cookies.set(k, v, domain=".instagram.com")
    return s


def post_photo_to_instagram(web_session: requests.Session, image_path: Path, caption: str, hashtags: list) -> dict:
    full_caption = caption + "\n\n" + " ".join(hashtags)
    upload_id    = str(int(time.time() * 1000))
    image_data   = image_path.read_bytes()

    # Upload image
    upload_resp = web_session.post(
        f"https://www.instagram.com/rupload_igphoto/fb_uploader_{upload_id}",
        data=image_data,
        headers={
            **web_session.headers,
            "X-Instagram-Rupload-Params": json.dumps({
                "media_type": 1, "upload_id": upload_id,
                "upload_media_height": 1024, "upload_media_width": 1024,
            }),
            "X-Entity-Type": "image/jpeg",
            "X-Entity-Name": f"fb_uploader_{upload_id}",
            "X-Entity-Length": str(len(image_data)),
            "Offset": "0",
            "Content-Type": "application/octet-stream",
        },
        timeout=60,
    )
    if upload_resp.status_code not in (200, 201):
        raise Exception(f"Upload failed {upload_resp.status_code}: {upload_resp.text[:200]}")
    print(f"  Upload OK: {upload_resp.json().get('status')}")

    time.sleep(2)

    # Publish
    cfg = web_session.post(
        "https://www.instagram.com/api/v1/media/configure/",
        data={"upload_id": upload_id, "caption": full_caption},
        headers={**web_session.headers, "Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if cfg.status_code not in (200, 201):
        raise Exception(f"Configure failed {cfg.status_code}: {cfg.text[:200]}")
    return cfg.json()


def run_poster(client, topic_data: dict):
    topic  = topic_data.get("topic", "")
    pillar = topic_data.get("pillar", "AI storytelling")
    print(f"\n[POSTER] Topic: {topic}")

    # 1. SEO Caption
    print("  Generating SEO/AEO caption with Claude...")
    caption  = generate_seo_caption(client, topic, pillar)
    hashtags = pick_hashtags(topic)
    print(f"  Caption ready ({len(caption)} chars), {len(hashtags)} hashtags.")

    # 2. Image
    print("  Generating image...")
    img_prompt = generate_image_prompt(client, topic)
    image_path = generate_image_hf(img_prompt)

    # 3. Post
    print("  Posting to Instagram...")
    web_session = load_web_session()
    result      = post_photo_to_instagram(web_session, image_path, caption, hashtags)
    media       = result.get("media", {})
    post_id     = str(media.get("pk", ""))
    shortcode   = media.get("code", "")
    print(f"  Posted! https://www.instagram.com/p/{shortcode}/")

    # 4. Record + possibly evolve
    record_post(post_id, shortcode, topic, caption, hashtags)
    if len(load_posted()) % EVOLUTION_AFTER_POSTS == 0:
        print("  Evolving content strategy...")
        evolve_strategy(client)

    return shortcode
