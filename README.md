# Robinhood Chain Meme Coin Screener (personal research tool)

Not financial advice. Chain ID 4663 (Robinhood Chain, Arbitrum Orbit L2).

## Fully free data stack -- no paid API required
- **Blockscout** (free key from dev.blockscout.com) -- holders, verification, deployer activity.
- **DexScreener** (no signup, no key at all) -- live price, liquidity, volume windows, buy/sell counts, new-token discovery. This replaced Codex, which required a paid activation fee.

## Two parts of this repo
- **Root** -- the Python data pipeline (blockscout_client.py, dexscreener_client.py, SQLite storage, the 0-90 composite scoring model with manipulation flags).
- **`web/`** -- a Next.js dashboard deployed on Vercel that displays `data/latest.json`.

## How it runs
`.github/workflows/poll.yml` runs every 15 minutes, executes `export_snapshot.py` (one poll cycle -> `data/latest.json`), and commits the result back to the repo. Vercel is linked to this repo's `main` branch and redeploys automatically on every push.

See `DEPLOY.md` for one-time setup steps.

## Local development (optional)
```bash
pip install -r requirements.txt
python main.py      # runs continuously, polls every 5 min
python report.py    # print current rankings from your local screener.db
```

## What to verify before trusting this for real decisions
- `bags_client.TOKEN_CREATED_TOPIC0` is a placeholder -- get the real event topic hash from BagsFactory's verified ABI before relying on it for launch discovery.
- Ownership-renounced / mint-blacklist checks and deployer-selling / co-funded-wallet flags are stubbed neutral in `scoring.py` -- extend once you've inspected a few real RH-chain memecoin contracts.
- Every scoring constant is a starting guess -- tune against real data.
- DexScreener rate limits: 60 req/min on `/token-profiles/latest/v1`, 300 req/min on `/token-pairs/v1/*`. Fine for a 15-min personal poll loop; don't lower the interval much below that with many tracked tokens.
