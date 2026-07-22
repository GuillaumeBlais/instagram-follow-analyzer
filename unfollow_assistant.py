"""
Manual unfollow assistant.

Merges the two target lists (Meta intersection + inactive candidates from
the notebook), deduplicates, prioritizes, and opens each profile in the
default browser one by one so YOU can click Unfollow manually.

Why manual clicks?
  Automated unfollow is the most-monitored TOS violation on Instagram.
  This tool assists but never automates the action — no risk for your account.

Progress is logged in LOG_CSV and can be resumed after interruption.
"""
import csv
import webbrowser
import time
from pathlib import Path
from datetime import datetime

from config import INTERSECTION_CSV, UNFOLLOW_CSV, LOG_CSV

PAUSE_AFTER_OPEN = 1.5  # seconds before prompt returns


def load_intersection():
    """Load accounts followed by both accounts (SAFE unfollow — access kept)."""
    if not Path(INTERSECTION_CSV).exists():
        print(f"ℹ️  {INTERSECTION_CSV} not found — skipping intersection source.")
        print(f"   (run intersection_meta.py first if you want this source)")
        return []
    rows = []
    with open(INTERSECTION_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            u = row.get("username", "").strip()
            rows.append({
                "username": u,
                "source": "🔗 COMMON (safe)",
                "priority": 1,
                "days_since_last_post": "",
                "followers": "",
                "biography": "",
                "score_unfollow": "",
                "profile_url": row.get("profile_url", "") or f"https://www.instagram.com/{u}/",
            })
    return rows


def load_unfollow_candidates():
    """Load unfollow candidates from the notebook (score > 60 or never posted)."""
    if not Path(UNFOLLOW_CSV).exists():
        print(f"ℹ️  {UNFOLLOW_CSV} not found — skipping notebook source.")
        print(f"   (run the Jupyter notebook first if you want this source)")
        return []
    rows = []
    with open(UNFOLLOW_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            u = row.get("username", "").strip()
            days = row.get("days_since_last_post", "")

            try:
                days_int = int(float(days)) if days else 0
                is_ghost = days_int >= 99999
            except Exception:
                is_ghost = False

            rows.append({
                "username": u,
                "source": "👻 NEVER POSTED" if is_ghost else "💀 DEAD (score>60)",
                "priority": 2 if is_ghost else 3,
                "days_since_last_post": days,
                "followers": row.get("followers", ""),
                "biography": (row.get("biography", "") or "")[:120],
                "score_unfollow": row.get("score_unfollow", ""),
                "profile_url": f"https://www.instagram.com/{u}/",
            })
    return rows


def load_already_processed():
    """Load usernames already processed (for resume after pause)."""
    if not Path(LOG_CSV).exists():
        return set()
    done = set()
    with open(LOG_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            done.add(row.get("username", "").lower().strip())
    return done


def log_decision(username, decision, source, notes=""):
    """Append a row to the log CSV."""
    is_new = not Path(LOG_CSV).exists()
    with open(LOG_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "username", "decision", "source", "notes"]
        )
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "username": username,
            "decision": decision,
            "source": source,
            "notes": notes,
        })


def deduplicate(rows):
    """Deduplicate by username, keeping highest priority (lowest number)."""
    by_username = {}
    for r in rows:
        u = r["username"].lower().strip()
        if not u:
            continue
        if u not in by_username or r["priority"] < by_username[u]["priority"]:
            if u in by_username:
                # Enrich with other source's info if missing
                for key in ("days_since_last_post", "followers", "biography", "score_unfollow"):
                    if not r.get(key) and by_username[u].get(key):
                        r[key] = by_username[u][key]
                # Merge sources
                if by_username[u]["source"] != r["source"]:
                    r["source"] = by_username[u]["source"] + " + " + r["source"]
            by_username[u] = r
    return sorted(by_username.values(), key=lambda x: (x["priority"], x["username"]))


def print_header():
    print("\n" + "=" * 70)
    print("🚀 UNFOLLOW ASSISTANT")
    print("=" * 70 + "\n")


def print_profile_info(row, current_idx, total, remaining):
    print("\n" + "─" * 70)
    print(f"[{current_idx}/{total}] Remaining : {remaining}")
    print("─" * 70)
    print(f"👤 @{row['username']}")
    print(f"🏷️  {row['source']}")
    if row.get("days_since_last_post"):
        days = row["days_since_last_post"]
        try:
            days_int = int(float(days))
            if days_int >= 99999:
                days_str = "NEVER posted"
            elif days_int > 365:
                days_str = f"{days_int}d ({days_int // 365} year+)"
            else:
                days_str = f"{days_int}d"
            print(f"📅 Last post : {days_str}")
        except Exception:
            pass
    if row.get("followers"):
        try:
            f = int(float(row["followers"]))
            if f > 1_000_000:
                f_str = f"{f/1_000_000:.1f}M"
            elif f > 1000:
                f_str = f"{f/1_000:.1f}k"
            else:
                f_str = str(f)
            print(f"👥 Followers : {f_str}")
        except Exception:
            print(f"👥 Followers : {row['followers']}")
    if row.get("biography"):
        print(f"📝 Bio : {row['biography']}")
    if row.get("score_unfollow"):
        print(f"⚡ Unfollow score : {row['score_unfollow']}")
    print(f"🌐 {row['profile_url']}\n")


def main():
    print_header()

    print("📂 Loading sources...")
    intersection = load_intersection()
    if intersection:
        print(f"   → {len(intersection)} accounts in common (Meta)")
    candidates = load_unfollow_candidates()
    if candidates:
        print(f"   → {len(candidates)} unfollow candidates (notebook)")

    all_rows = intersection + candidates
    if not all_rows:
        print("\n❌ No source data available. Nothing to process.")
        return

    all_rows = deduplicate(all_rows)
    print(f"   → {len(all_rows)} unique accounts after dedup")

    already_done = load_already_processed()
    if already_done:
        print(f"   → {len(already_done)} previously processed (skipped)")
    to_process = [r for r in all_rows if r["username"].lower().strip() not in already_done]

    if not to_process:
        print("\n✅ All accounts have already been processed !")
        return

    total = len(to_process)
    print(f"\n🎯 {total} accounts to process in this session\n")
    print("Priority order :")
    print("  1️⃣  Common with secondary account (safe — access kept)")
    print("  2️⃣  Never posted (ghosts)")
    print("  3️⃣  Confirmed dead (score > 60)")

    print("\nAvailable commands :")
    print("  [Enter]  = unfollow done, next")
    print("  k        = keep (log KEEP)")
    print("  s        = skip (indecisive, log SKIP)")
    print("  o        = reopen profile in browser")
    print("  q        = quit cleanly (progress saved)")

    input("\n👉 Press Enter to start...")

    for i, row in enumerate(to_process, start=1):
        remaining = total - i
        print_profile_info(row, i, total, remaining)

        webbrowser.open(row["profile_url"])
        time.sleep(PAUSE_AFTER_OPEN)

        while True:
            action = input(
                "👉 Action [Enter=unfollow ok / k=keep / s=skip / o=reopen / q=quit] : "
            ).strip().lower()

            if action == "":
                log_decision(row["username"], "UNFOLLOW", row["source"])
                print(f"   ✅ {row['username']} → UNFOLLOW logged")
                break
            elif action == "k":
                log_decision(row["username"], "KEEP", row["source"])
                print(f"   💾 {row['username']} → KEEP logged")
                break
            elif action == "s":
                log_decision(row["username"], "SKIP", row["source"])
                print(f"   ⏭️  {row['username']} → SKIP logged")
                break
            elif action == "o":
                webbrowser.open(row["profile_url"])
                print("   🔄 Profile reopened")
                continue
            elif action == "q":
                print(f"\n👋 Session interrupted. {i-1} processed, {total-i+1} left.")
                print(f"   Log : {LOG_CSV}")
                print("   Relaunch the script to resume.")
                return

    print(f"\n🎉 SESSION COMPLETE — {total} accounts processed !")
    print(f"   Full log : {LOG_CSV}")

    stats = {"UNFOLLOW": 0, "KEEP": 0, "SKIP": 0}
    with open(LOG_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            d = row.get("decision", "")
            if d in stats:
                stats[d] += 1
    print(f"\n📊 Total recap :")
    print(f"   ✅ UNFOLLOW : {stats['UNFOLLOW']}")
    print(f"   💾 KEEP     : {stats['KEEP']}")
    print(f"   ⏭️  SKIP     : {stats['SKIP']}")


if __name__ == "__main__":
    main()
