"""Run from GitHub Actions to create a cloud-IP instagrapi session."""
import os, sys, json, time
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ChallengeUnknownStep
from pathlib import Path

username = os.environ["IG_USERNAME"]
password = os.environ["IG_PASSWORD"]

print(f"Logging in as {username}...")
cl = Client()
cl.delay_range = [1, 3]

MAX_RETRIES = 3
for attempt in range(1, MAX_RETRIES + 1):
    try:
        cl.login(username, password)
        print(f"Login OK  user_id={cl.user_id}")
        break
    except ChallengeUnknownStep as e:
        if attempt < MAX_RETRIES:
            print(f"\n[!] Instagram challenge sent to your phone app (attempt {attempt}/{MAX_RETRIES}).")
            print(f"[!]   Open Instagram app as @{username}")
            print(f"[!]   Tap 'This was me' on the suspicious login notification")
            print(f"[!]   Waiting 90 seconds for you to approve...")
            time.sleep(90)
            print("[!]   Retrying login...")
        else:
            print(f"\n[!] All {MAX_RETRIES} attempts failed. Challenge not resolved.")
            print(f"[!]   Open Instagram app as @{username} → approve the login → re-run login.yml")
            sys.exit(3)
    except ChallengeRequired as e:
        print(f"[!] Challenge required (type: {type(e).__name__}) — attempt {attempt}")
        if attempt < MAX_RETRIES:
            print("[!] Waiting 30s before retry...")
            time.sleep(30)
        else:
            print("[!] All retries failed.")
            sys.exit(3)
    except Exception as e:
        print(f"[!] Login error: {e}")
        sys.exit(1)

settings = cl.get_settings()
data = {"_instagrapi": settings, "user_id": str(cl.user_id)}
Path("ig_settings.json").write_text(json.dumps(data, indent=2))
print("ig_settings.json saved")
