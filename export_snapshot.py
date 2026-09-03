"""
Runs one poll cycle, then dumps the current rankings to data/latest.json
so the Next.js site (deployed on Vercel) has something to read.
Called by .github/workflows/poll.yml on a schedule.
"""
import json
import time
import os

from storage import init_db, get_conn
from poller import run_cycle

QUERY = """
SELECT t.symbol, t.address, s.final_score, s.recommended, s.flags, s.ts
FROM scores s
JOIN tokens t ON t.address = s.address
WHERE s.ts = (SELECT MAX(ts) FROM scores s2 WHERE s2.address = s.address)
ORDER BY s.final_score DESC;
"""

if __name__ == "__main__":
    init_db()
    run_cycle()

    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(QUERY).fetchall()]

    out = {"last_updated": int(time.time()), "tokens": rows}

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote data/latest.json with {len(rows)} tokens.")
