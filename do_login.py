"""Run from GitHub Actions to create a cloud-IP instagrapi session."""
import os, json
from instagrapi import Client
from pathlib import Path

username = os.environ["IG_USERNAME"]
password = os.environ["IG_PASSWORD"]

print(f"Logging in as {username}...")
cl = Client()
cl.delay_range = [1, 3]
cl.login(username, password)
print(f"Login OK  user_id={cl.user_id}")

settings = cl.get_settings()
data = {"_instagrapi": settings, "user_id": str(cl.user_id)}
Path("ig_settings.json").write_text(json.dumps(data, indent=2))
print("ig_settings.json saved")
