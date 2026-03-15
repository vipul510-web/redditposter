# Reddit Comment Bot

An automated way to post **contextual** (not spammy) comments on relevant Reddit posts within specified subreddits and topics. Fully configurable via `config.yaml`.

## Features

- **Config-driven**: Subreddits and topics defined in `config.yaml`
- **Topic matching**: Only comments on posts relevant to your configured topics (keyword-based)
- **Contextual comments**: Template-based or AI-generated (OpenAI/Anthropic) for natural replies
- **Anti-spam safeguards**: Rate limiting, max comments per run, skip already-commented posts
- **Quality filters**: Min post score, max post age, max existing comments

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Reddit API credentials

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Create an app (choose "script" type)
3. Note your `client_id` (under the app name) and `client_secret`

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

Edit `config.yaml`:

- **subreddits**: List of subreddits to monitor (e.g. `learnpython`, `Python`)
- **topics**: Topics with keywords and optional comment guidance/templates

### 4. Optional: AI-generated comments

For truly contextual, natural comments, use an LLM:

- Set `comment_mode: openai` or `comment_mode: anthropic` in `config.yaml`
- Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to `.env`
- Install: `pip install openai` or `pip install anthropic`

## Usage

```bash
# Dry run - see what would be commented (no posting)
python main.py --dry-run

# Single run
python main.py

# Run every hour
python main.py --loop 3600
```

## Config reference

| Setting | Description |
|--------|-------------|
| `subreddits` | List of subreddit names (no r/ prefix) |
| `topics[].keywords` | Keywords that must appear in post title/body |
| `topics[].comment_guidance` | Guidance for AI comment generation |
| `topics[].templates` | Per-topic templates (template mode) |
| `settings.min_post_score` | Skip posts below this score |
| `settings.max_post_age_hours` | Don't comment on older posts |
| `settings.delay_between_comments` | Seconds between comments (rate limit) |
| `settings.max_comments_per_run` | Safety cap per run |
| `comment_mode` | `template`, `openai`, or `anthropic` |

## Reddit rules

- Use a descriptive User-Agent (included)
- Respect rate limits (~60 requests/min for OAuth)
- Don't spam: keep `delay_between_comments` and `max_comments_per_run` conservative
- Follow each subreddit's rules

## Running in the cloud (GitHub Actions)

You can run the bot on GitHub's servers so it works without your laptop. It runs on a schedule (e.g. every 4 hours).

### Setup

1. **Push this repo to GitHub** (create a new repo and push your code).

2. **Add secrets** in your repo: Settings → Secrets and variables → Actions → New repository secret. Add:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USERNAME`
   - `REDDIT_PASSWORD`
   - `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` (only if using AI comment mode)

3. **Adjust the schedule** in `.github/workflows/reddit-bot.yml` if needed. Default is every 4 hours:
   ```yaml
   - cron: "0 */4 * * *"   # Every 4 hours
   ```

4. The workflow runs automatically on schedule. You can also trigger it manually: Actions → Reddit Comment Bot → Run workflow.

GitHub Actions free tier includes 2,000 minutes/month for private repos (plenty for a bot that runs every few hours).

## Scheduling (cron) – local/VM

For periodic runs on your own machine or a server:

```cron
# Run every 4 hours
0 */4 * * * cd /path/to/redditcommentor && python main.py
```
