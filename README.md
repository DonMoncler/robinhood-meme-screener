# Robinhood Chain Meme Coin Screener (personal research tool)

Not financial advice. Chain ID 4663 (Robinhood Chain, Arbitrum Orbit L2).

## Two parts of this repo
- **Root** -- the Python data pipeline (Blockscout + Codex clients, SQLite storage, the 0-90 composite scoring model with manipulation flags).
- **`web/`** -- a Next.js dashboard deployed on Vercel that displays `data/latest.json`.

## How it runs
`.github/workflows/poll.yml` runs every 15 minutes, executes `export_snapshot.py` (one poll cycle -> `data/latest.json`), and commits the result back to the repo. Vercel is linked to this repo's `main` branch and redeploys automatically on every push, so the site always shows the latest commit's data.

See `DEPLOY.md` for one-time setup steps (API keys as GitHub secrets, Vercel root directory, password protection).

## Local development (optional)
```bash
pip install -r requirements.txt
python main.py      # runs continuously, polls every 5 min
python report.py    # print current rankings from your local screener.db
```

## What to verify before trusting this for real decisions
- Codex's GraphQL field names in `codex_client.py` are built from documented query *names* -- confirm exact fields in Codex's GraphQL Explorer (docs.codex.io/explore).
- `bags_client.TOKEN_CREATED_TOPIC0` is a placeholder -- get the real event topic hash from BagsFactory's verified ABI before relying on it.
- Ownership-renounced / mint-blacklist checks and deployer-selling / co-funded-wallet flags are stubbed neutral in `scoring.py` -- extend once you've inspected a few real RH-chain memecoin contracts.
- Every scoring constant is a starting guess -- tune against real data.
