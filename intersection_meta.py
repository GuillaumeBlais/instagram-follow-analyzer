"""
Cross-reference tool for two Instagram Meta Data Downloads.

Extracts the intersection of accounts followed by TWO accounts,
using the official Meta Data Download (JSON format).

Use case: identify accounts followed by both a MAIN and a SECONDARY account,
so they can be safely unfollowed from the main one (access preserved via
the secondary).

Setup:
  1. Request a Meta Data Download for each account
     (Instagram → Settings → Download your information → JSON)
  2. Unzip both archives into folders defined in config.py
     (EXTRACT_DIR_MAIN and EXTRACT_DIR_SECONDARY)
  3. Run this script
"""
import json
import csv
from pathlib import Path
from datetime import datetime, timezone

from config import EXTRACT_DIR_MAIN, EXTRACT_DIR_SECONDARY, INTERSECTION_CSV


def find_json_file(root_dir, filename):
    """Recursively find a JSON file by name."""
    matches = list(Path(root_dir).rglob(filename))
    return matches[0] if matches else None


def extract_following(root_dir):
    """
    Extract follows from following.json.
    Meta 2026 format: username in `title`, timestamp in `string_list_data`.
    """
    json_file = find_json_file(root_dir, "following.json")
    if not json_file:
        print(f"   ⚠️ following.json not found in {root_dir}")
        return {}

    print(f"   📄 {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("relationships_following", []) if isinstance(data, dict) else data

    result = {}
    for item in entries:
        username = (item.get("title") or "").lower().strip()
        if not username and item.get("string_list_data"):
            # Legacy format fallback
            username = (item["string_list_data"][0].get("value") or "").lower().strip()
        if not username:
            continue

        href = ""
        ts = 0
        if item.get("string_list_data"):
            first = item["string_list_data"][0]
            href = first.get("href", "").replace("/_u/", "/")
            ts = first.get("timestamp", 0)

        result[username] = {
            "profile_url": href or f"https://www.instagram.com/{username}/",
            "followed_since": datetime.fromtimestamp(ts, tz=timezone.utc)
                .strftime("%Y-%m-%d") if ts else "",
        }
    return result


def main():
    print("🎯 Extracting common follows between two accounts\n")

    main_follows = extract_following(EXTRACT_DIR_MAIN)
    secondary_follows = extract_following(EXTRACT_DIR_SECONDARY)

    print(f"\nMain account follows      : {len(main_follows)}")
    print(f"Secondary account follows : {len(secondary_follows)}")

    common = set(main_follows.keys()) & set(secondary_follows.keys())
    print(f"\n✅ In common              : {len(common)} accounts\n")

    rows = []
    for u in sorted(common):
        rows.append({
            "username": u,
            "profile_url": main_follows[u]["profile_url"],
            "followed_by_main_since": main_follows[u]["followed_since"],
            "followed_by_secondary_since": secondary_follows[u]["followed_since"],
        })

    if rows:
        with open(INTERSECTION_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Export → {INTERSECTION_CSV} ({len(rows)} rows)")
        print(f"\nThese accounts can be safely unfollowed from the main account:")
        print(f"access remains via the secondary account.")
    else:
        print("⚠️ No accounts in common.")


if __name__ == "__main__":
    main()
