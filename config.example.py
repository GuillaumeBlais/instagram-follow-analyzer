"""
Configuration file — TEMPLATE.

📋 Setup:
   1. Copy this file to `config.py`
   2. Fill in your own Instagram usernames and file paths
   3. `config.py` is git-ignored — your data stays private

⚠️ NEVER commit `config.py` to any public repo.
"""

# ---------- INSTAGRAM ACCOUNTS ----------

# Account used to log in via instaloader (recommended: a SECONDARY account,
# not your main one — reduces ban risk)
SESSION_USER = "your_scraper_account"

# Local session filename (created by instaloader or import_firefox_session.py)
SESSION_FILE = "session-your_scraper_account"

# Main account whose follows you want to analyze
TARGET_USER = "your_main_account"


# ---------- META DATA DOWNLOAD ----------
# Extracted folders from Instagram Data Download ZIPs
# (Instagram → Settings → Download your information → JSON format)

# Extract of the secondary account's Meta Download
EXTRACT_DIR_SECONDARY = "meta_secondary"

# Extract of the main account's Meta Download
EXTRACT_DIR_MAIN = "meta_main"


# ---------- OUTPUT FILES ----------

SCAN_CSV = "follows_activity.csv"
INTERSECTION_CSV = "common_follows.csv"
UNFOLLOW_CSV = "a_unfollow.csv"
LOG_CSV = "unfollow_log.csv"


# ---------- RATE LIMITS ----------

# Seconds between each profile visit during scan
SLEEP_BETWEEN = 3

# Posts checked per profile (handles up to 3 pinned posts)
POSTS_TO_CHECK = 6

# Checkpoint frequency (every N profiles)
CHECKPOINT_EVERY = 20
