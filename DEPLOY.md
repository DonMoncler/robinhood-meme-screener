# Deploying the dashboard (Vercel + GitHub Actions)

## How the pieces connect
1. GitHub Actions (`.github/workflows/poll.yml`) runs every 15 minutes, executes `export_snapshot.py` (pulling from Blockscout + DexScreener, both free), and commits `data/latest.json` back to the repo.
2. Vercel is linked to the repo's `main` branch and auto-redeploys the `web/` Next.js app on every push.
3. The site's `/api/data` route fetches `data/latest.json` from GitHub's raw content CDN.

## One-time setup
1. Repo Settings -> Secrets and variables -> Actions -> add `BLOCKSCOUT_API_KEY` (free from dev.blockscout.com). No Codex key needed -- DexScreener requires no signup at all.
2. Actions tab -> run `poll-and-publish` manually once so `data/latest.json` has real data before checking the live site.
3. Vercel project settings -> Root Directory -> `web`.
4. Site is protected via `web/middleware.js` (HTTP Basic Auth) since Advanced Deployment Protection needs a paid Vercel plan. Set `SITE_USER` / `SITE_PASSWORD` as Vercel environment variables to override the code defaults.

## Known limitation
Committing `screener.db` every 15 min keeps things simple but will grow the repo's git history over time. If that becomes an issue, swap `storage.py`'s SQLite calls for a hosted option like Turso (libSQL) -- same SQL, no repo bloat. Not needed to get this running.
