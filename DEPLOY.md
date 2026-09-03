# Deploying the dashboard (Vercel + GitHub Actions)

## How the pieces connect
1. GitHub Actions (`.github/workflows/poll.yml`) runs every 15 minutes, executes `export_snapshot.py`, and commits `data/latest.json` back to the repo.
2. Vercel is linked to the repo's `main` branch and auto-redeploys the `web/` Next.js app on every push.
3. The site's `/api/data` route fetches `data/latest.json` from GitHub's raw content CDN.

## One-time setup
1. Repo Settings -> Secrets and variables -> Actions -> add `BLOCKSCOUT_API_KEY`, `CODEX_API_KEY`, optionally `TELEGRAM_BOT_TOKEN` / `TWITTER_BEARER_TOKEN`.
2. Actions tab -> run `poll-and-publish` manually once so `data/latest.json` has real data before checking the live site.
3. Vercel project settings -> Root Directory -> `web`.
4. Vercel project settings -> Deployment Protection -> turn on password protection (personal tool, URL shouldn't be publicly viewable).

## Known limitation
Committing `screener.db` every 15 min keeps things simple but will grow the repo's git history over time. If that becomes an issue, swap `storage.py`'s SQLite calls for a hosted option like Turso (libSQL) -- same SQL, no repo bloat. Not needed to get this running.
