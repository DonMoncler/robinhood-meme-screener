"""
Quick CLI to see current standings. Run: python report.py
"""
from storage import get_conn

QUERY = """
SELECT t.symbol, t.address, s.final_score, s.recommended, s.flags, s.ts
FROM scores s
JOIN tokens t ON t.address = s.address
WHERE s.ts = (SELECT MAX(ts) FROM scores s2 WHERE s2.address = s.address)
ORDER BY s.final_score DESC;
"""

if __name__ == "__main__":
    with get_conn() as conn:
        rows = conn.execute(QUERY).fetchall()
    print(f"{'SYMBOL':<10}{'SCORE':<8}{'REC':<5}{'FLAGS'}")
    for r in rows:
        print(f"{(r['symbol'] or '?'):<10}{r['final_score']:<8}{r['recommended']:<5}{r['flags']}")
