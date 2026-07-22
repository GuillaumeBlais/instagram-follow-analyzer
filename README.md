# 📊 Instagram Follows Analyzer

A Python toolkit to analyze the accounts you follow on Instagram, identify
inactive/ghost accounts, cross-reference multiple accounts, and manually
clean up your follows list — **safely and without automation risks**.

## ✨ Features

- 🔍 **Deep scan** of every followed account: last-post date (handles pinned
  posts), engagement rate, profile metadata, life signals (stories, highlights).
- 📊 **Data-rich CSV export** ready for analysis in Jupyter / Excel / pandas.
- 📓 **Jupyter notebook** with distribution charts, thematic clustering,
  anomaly detection, and composite unfollow score.
- 🔗 **Cross-reference two accounts** via official Meta Data Downloads
  to find common follows (safe unfollow targets).
- 🖱️ **Manual unfollow assistant** that opens each candidate profile in your
  browser one at a time — **you** click Unfollow, keeping your account safe
  from automation bans.
- 💾 **Checkpoints & resume** everywhere — safe to interrupt and restart.

## ⚠️ Philosophy

**No automated unfollow.** Automated actions are the most-monitored TOS
violation on Instagram and put your account at real risk of shadowban/ban.
This toolkit assists your decisions but never clicks Unfollow for you.

## 🧰 Requirements

- Python 3.10+
- Firefox (recommended for session import)
- An Instagram account you can use for scraping (ideally a **secondary** one)

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/insta-follow-analyzer.git
cd insta-follow-analyzer

python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.py config.py
# Edit config.py with your usernames (git-ignored, stays private)
```

### 3. Import your Instagram session from Firefox

Log in to Instagram in Firefox with your scraper account, then close Firefox
completely and run:

```bash
python import_firefox_session.py -f session-YOUR_SCRAPER_USERNAME
```

### 4. Scan the follows

```bash
python analyze_follows.py
```

For ~800 follows, expect **~1h30 of scan time** (3 s/profile rate limit).
Interrupt with Ctrl+C anytime — checkpoints allow resuming.

Output: `follows_activity.csv`

### 5. Analyze in Jupyter (optional)

```bash
jupyter notebook analyze_follows_notebook.ipynb
```

Or open the notebook directly in VS Code (Jupyter extension is built-in).
Run all cells → get distribution charts, unfollow score, categorized lists.

### 6. Cross-reference with a second account (optional)

If you have another Instagram account and want to find common follows
(safe unfollow candidates — access preserved via the other account):

1. Request a Meta Data Download for **both** accounts:
   *Instagram → Settings → Accounts Center → Your information → Download
   your information → JSON format*
2. Unzip both archives into the folders defined in `config.py`
3. Run:

```bash
python intersection_meta.py
```

Output: `common_follows.csv`

### 7. Manual unfollow session

```bash
python unfollow_assistant.py
```

- Merges & deduplicates candidates from both sources
- Opens each profile in your default browser one at a time
- Shows key metrics in terminal
- Waits for your keyboard input:
  - `Enter` = "I unfollowed, next"
  - `k` = keep
  - `s` = skip (indecisive)
  - `o` = reopen profile
  - `q` = quit (progress saved)
- Logs every decision to `unfollow_log.csv` with timestamps
- **Never clicks Unfollow for you** — safe for your account

**Rate limit reminder:** Instagram tolerates ~50–60 unfollows per hour.
Take breaks during long sessions.

## 📁 Files

| File | Purpose |
|---|---|
| `analyze_follows.py` | Main scanner with checkpointing |
| `intersection_meta.py` | Cross-reference two Meta Data Downloads |
| `unfollow_assistant.py` | Manual unfollow session helper |
| `analyze_follows_notebook.ipynb` | Jupyter analysis notebook |
| `import_firefox_session.py` | Firefox → instaloader session bridge (from instaloader project) |
| `config.example.py` | Config template — copy to `config.py` |
| `requirements.txt` | Python dependencies |

## 🔒 What's in `.gitignore`

To protect your privacy:
- `config.py` (your usernames)
- `session-*` (auth cookies)
- `*.csv` (all scan results & personal data)
- `instagram-*.zip` and `meta_*/` (Meta Data Downloads)
- `checkpoint*.json` (scan progress)
- `unfollow_log.csv` (your decisions)

**Always verify** with `git status` before committing that no sensitive
files are staged.

## 📊 Sample analytical output

The Jupyter notebook produces summaries like:

```
📌 Total follows analyzed        : 818
✅ Analyzable (OK)               : 706
🔒 Private inaccessible          : 104
💀 Never posted                  : 8

📅 ACTIVITY
  - Active (<7d)        : 415
  - Semi-active (7-90d) : 165
  - Dormant (90-365d)   : 52
  - Dead (>1y)          : 73

🎯 RECOMMENDATIONS
  - To unfollow (score>60)      : 42
  - Never posted (obvious)      : 8
```

## 🐛 Troubleshooting

**`Login: Checkpoint required`** on session creation
: Use the Firefox session import method (`import_firefox_session.py`)
  instead of `instaloader --login`. Instagram trusts browser-established
  sessions more.

**`429 Too Many Requests`** or `feedback_required`
: You've hit the rate limit. Wait 1–3 hours, then resume — the checkpoint
  system preserves your progress.

**Notebook `TypeError` on datetime**
: Ensure you're using Python 3.10+ — the `datetime.timezone` handling
  requires timezone-aware objects throughout.

## ⚖️ Disclaimer

This project is for **personal use only**. It uses Instagram's public
data and Meta's official data-download feature. Automated scraping may
be against Instagram's Terms of Service depending on your use — use
responsibly, respect rate limits, and prefer a secondary account for scans.

The author is **not affiliated with Meta or Instagram** and takes no
responsibility for account restrictions resulting from use of this tool.

## 📄 License

MIT
