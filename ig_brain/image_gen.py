"""
Image generation using HuggingFace free FLUX model.
Falls back to PIL-styled card if HF is unavailable.
"""
import time
import requests
from pathlib import Path
from .config import IMAGES_DIR


HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
HF_HEADERS = {"Content-Type": "application/json"}  # no token needed for public models


def generate_image_hf(prompt: str) -> Path:
    """Try HuggingFace FLUX first; fall back to PIL card on any error."""
    print(f"  Generating image via HuggingFace FLUX...")
    try:
        payload = {"inputs": prompt, "parameters": {"width": 1024, "height": 1024}}
        resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            filename = IMAGES_DIR / f"post_{int(time.time())}.jpg"
            filename.write_bytes(resp.content)
            print(f"  HF image saved: {filename}")
            return filename
        elif resp.status_code == 503:
            print(f"  HF model loading, retrying once...")
            time.sleep(20)
            resp = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=90)
            if resp.status_code == 200 and resp.headers.get("content-type","").startswith("image"):
                filename = IMAGES_DIR / f"post_{int(time.time())}.jpg"
                filename.write_bytes(resp.content)
                return filename
    except Exception as e:
        print(f"  HF unavailable ({type(e).__name__}), using PIL card.")

    return generate_image_pil(prompt)


def generate_image_pil(prompt: str) -> Path:
    """Generate a cinematic dark-style text card using PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import textwrap, math

        W, H = 1080, 1080
        img  = Image.new("RGB", (W, H), (8, 6, 18))
        draw = ImageDraw.Draw(img)

        # Dark purple-to-black radial-like gradient via horizontal bands
        for y in range(H):
            t = y / H
            r = int(8  + 30  * math.sin(t * math.pi))
            g = int(6  + 10  * math.sin(t * math.pi))
            b = int(18 + 50  * math.sin(t * math.pi))
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Decorative border lines
        for offset, color in [(30,(60,40,100)),(36,(40,25,70)),(42,(25,15,50))]:
            draw.rectangle([offset, offset, W-offset, H-offset], outline=color, width=1)

        # Glowing centre circle hint
        for radius in range(300, 250, -10):
            alpha = int((300 - radius) * 0.8)
            draw.ellipse([W//2-radius, H//2-radius, W//2+radius, H//2+radius],
                         outline=(alpha, int(alpha*0.6), int(alpha*1.5)), width=1)

        # Topic text — clean, large, centered
        words   = prompt.replace("cinematic","").replace("dramatic","").strip()
        wrapped = textwrap.wrap(words[:120], width=18)
        y_pos   = H//2 - len(wrapped)*45
        for line in wrapped[:5]:
            # Shadow
            draw.text((W//2+2, y_pos+2), line.upper(), fill=(20,10,40), anchor="mm")
            # Main text
            draw.text((W//2, y_pos), line.upper(), fill=(220, 200, 255), anchor="mm")
            y_pos += 90

        # Horizontal divider
        draw.line([(W//2-120, H-140), (W//2+120, H-140)], fill=(100, 80, 160), width=1)

        # Brand name
        draw.text((W//2, H-100), "story.matters_", fill=(160, 140, 220), anchor="mm")
        draw.text((W//2, H-68),  "AI · Storytelling · Imagination", fill=(80, 65, 120), anchor="mm")

        filename = IMAGES_DIR / f"post_{int(time.time())}.jpg"
        img.save(filename, "JPEG", quality=95)
        print(f"  PIL card saved: {filename}")
        return filename

    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
        return generate_image_pil(prompt)
