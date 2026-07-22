"""
Instagram follows analyzer.

Scans every account followed by TARGET_USER via instaloader.
For each followee, extracts:
  - Profile metadata (bio, business category, followers/following ratio)
  - Life signals (public story, highlights)
  - Latest post (handles pinned posts — up to 3 in Instagram)
  - Engagement rate on the latest post

Outputs a CSV sorted by inactivity (most inactive first).

Requires a valid instaloader session (see import_firefox_session.py
or run `instaloader --login=SESSION_USER` first).

Configuration: see config.py (copy from config.example.py).
"""
import csv
import json
import time
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

import instaloader

from config import (
    SESSION_USER, SESSION_FILE, TARGET_USER,
    SCAN_CSV, SLEEP_BETWEEN, POSTS_TO_CHECK, CHECKPOINT_EVERY,
)

CHECKPOINT_FILE = "checkpoint.json"


def load_checkpoint():
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed": [], "results": []}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)


def safe_getattr(obj, name, default=None):
    """Read an attribute without crashing on API variations."""
    try:
        val = getattr(obj, name, default)
        return val if val is not None else default
    except Exception:
        return default


def analyze_followee(followee):
    """Extract as many exploitable data points as possible for a followee."""
    now = datetime.now(timezone.utc)

    # Profile metadata (free — already loaded)
    followers = safe_getattr(followee, "followers", 0) or 0
    followees_count = safe_getattr(followee, "followees", 0) or 0
    posts_count = safe_getattr(followee, "mediacount", 0) or 0

    base = {
        # Identity
        "username": followee.username,
        "full_name": safe_getattr(followee, "full_name", ""),
        "biography": (safe_getattr(followee, "biography", "") or "")
            .replace("\n", " ").replace("\r", " ")[:500],
        "external_url": safe_getattr(followee, "external_url", ""),
        # Status
        "is_private": safe_getattr(followee, "is_private", False),
        "is_verified": safe_getattr(followee, "is_verified", False),
        "is_business": safe_getattr(followee, "is_business_account", False),
        "business_category": safe_getattr(followee, "business_category_name", ""),
        # Volumes
        "followers": followers,
        "following": followees_count,
        "posts_count": posts_count,
        "igtv_count": safe_getattr(followee, "igtvcount", 0) or 0,
        # Ratios
        "ratio_followers_following": round(followers / followees_count, 2)
            if followees_count else None,
        # Life signals
        "has_public_story": safe_getattr(followee, "has_public_story", False),
        "has_highlights": safe_getattr(followee, "has_highlight_reels", False),
        # Latest post (filled below)
        "last_post_utc": None,
        "days_since_last_post": None,
        "last_post_type": None,
        "last_post_is_video": None,
        "last_post_likes": None,
        "last_post_comments": None,
        "last_post_engagement_rate_pct": None,
        "pinned_posts_detected": 0,
        # Analysis status
        "status": "OK",
    }

    # Edge cases
    if base["is_private"] and not safe_getattr(followee, "followed_by_viewer", False):
        base["status"] = "PRIVATE_NO_ACCESS"
        return base

    if posts_count == 0:
        base["status"] = "NEVER_POSTED"
        base["days_since_last_post"] = 99999
        return base

    # Latest post (accounts for pinned posts)
    # Instagram allows up to 3 pinned posts at the top of a profile.
    # get_posts() returns them FIRST regardless of their actual date.
    # We check the N first posts and keep the one with the most recent date.
    try:
        first_posts = list(islice(followee.get_posts(), POSTS_TO_CHECK))
        if first_posts:
            latest_post = max(first_posts, key=lambda p: p.date_utc)
            post_date = latest_post.date_utc.replace(tzinfo=timezone.utc)

            base["last_post_utc"] = post_date.isoformat()
            base["days_since_last_post"] = (now - post_date).days
            base["last_post_type"] = safe_getattr(latest_post, "typename", "")
            base["last_post_is_video"] = safe_getattr(latest_post, "is_video", False)
            likes = safe_getattr(latest_post, "likes", 0) or 0
            comments = safe_getattr(latest_post, "comments", 0) or 0
            base["last_post_likes"] = likes
            base["last_post_comments"] = comments
            if followers > 0:
                base["last_post_engagement_rate_pct"] = round(
                    100 * (likes + comments) / followers, 3
                )

            # A post is "pinned" if it appears BEFORE a more recent post
            base["pinned_posts_detected"] = sum(
                1 for i, p in enumerate(first_posts)
                if any(later.date_utc > p.date_utc for later in first_posts[i + 1:])
            )
    except Exception as e:
        base["status"] = f"ERROR: {type(e).__name__}"

    return base


def main():
    print(f"🚀 Analyzing follows of @{TARGET_USER}")
    print(f"   Session : @{SESSION_USER} (file: {SESSION_FILE})")
    print(f"   Sleep between profiles : {SLEEP_BETWEEN}s")
    print(f"   Posts checked per profile : {POSTS_TO_CHECK} (handles pinned)\n")

    L = instaloader.Instaloader(
        quiet=True,
        download_pictures=False, download_videos=False,
        download_video_thumbnails=False, download_geotags=False,
        download_comments=False, save_metadata=False, compress_json=False,
    )

    try:
        L.load_session_from_file(SESSION_USER, filename=SESSION_FILE)
        print(f"✅ Session loaded\n")
    except FileNotFoundError:
        print(f"❌ Session file '{SESSION_FILE}' not found.")
        print(f"   Run first : python import_firefox_session.py -f {SESSION_FILE}")
        return

    try:
        target = instaloader.Profile.from_username(L.context, TARGET_USER)
    except Exception as e:
        print(f"❌ Cannot access @{TARGET_USER} : {e}")
        return

    total = target.followees
    print(f"📊 {total} followees to analyze.\n")

    state = load_checkpoint()
    already_done = set(state["processed"])
    if already_done:
        print(f"⏩ Resuming : {len(already_done)} already processed.\n")

    try:
        for i, followee in enumerate(target.get_followees(), start=1):
            if followee.username in already_done:
                continue

            print(f"[{i}/{total}] @{followee.username}...", end=" ", flush=True)
            data = analyze_followee(followee)
            state["results"].append(data)
            state["processed"].append(followee.username)

            status_msg = data["status"]
            if data["days_since_last_post"] is not None and status_msg == "OK":
                er = data.get("last_post_engagement_rate_pct")
                er_str = f" | ER {er}%" if er is not None else ""
                pinned = data.get("pinned_posts_detected", 0)
                pin_str = f" | 📌{pinned}" if pinned > 0 else ""
                status_msg = f"{data['days_since_last_post']}d{er_str}{pin_str}"
            print(status_msg)

            if i % CHECKPOINT_EVERY == 0:
                save_checkpoint(state)
                print(f"   💾 Checkpoint saved ({len(state['processed'])} processed)")

            time.sleep(SLEEP_BETWEEN)

    except KeyboardInterrupt:
        print("\n⏸️  Manual interrupt. Progress saved.")
    except Exception as e:
        print(f"\n⚠️  Error : {e}. Progress saved.")
    finally:
        save_checkpoint(state)

    # Export CSV sorted by inactivity
    results = state["results"]
    results.sort(
        key=lambda x: x.get("days_since_last_post")
            if x.get("days_since_last_post") is not None else -1,
        reverse=True,
    )

    if results:
        with open(SCAN_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✅ Export → {SCAN_CSV} ({len(results)} rows)")
    else:
        print("\n⚠️ No results.")


if __name__ == "__main__":
    main()
