"""
SQLite storage layer.
Every poll cycle writes one row per token into `snapshots` -- this table
IS the time series. Nothing is ever overwritten.
"""
import sqlite3
import time
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens (
    address     TEXT PRIMARY KEY,
    symbol      TEXT,
    name        TEXT,
    deployer    TEXT,
    deploy_ts   INTEGER,
    verified    INTEGER DEFAULT 0,
    first_seen  INTEGER
);

CREATE TABLE IF NOT EXISTS snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    address         TEXT NOT NULL,
    ts              INTEGER NOT NULL,
    price_usd       REAL,
    liquidity_usd   REAL,
    volume_1h_usd   REAL,
    volume_6h_usd   REAL,
    volume_24h_usd  REAL,
    buys_1h         INTEGER,
    sells_1h        INTEGER,
    holder_count    INTEGER,
    top10_pct       REAL,
    FOREIGN KEY(address) REFERENCES tokens(address)
);
CREATE INDEX IF NOT EXISTS idx_snap_addr_ts ON snapshots(address, ts);

CREATE TABLE IF NOT EXISTS social_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    address         TEXT NOT NULL,
    ts              INTEGER NOT NULL,
    mentions_count  INTEGER,
    distinct_authors INTEGER,
    followers_sum   INTEGER,
    engagement_sum  INTEGER
);
CREATE INDEX IF NOT EXISTS idx_social_addr_ts ON social_snapshots(address, ts);

CREATE TABLE IF NOT EXISTS scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    address         TEXT NOT NULL,
    ts              INTEGER NOT NULL,
    liquidity_score REAL,
    holder_score    REAL,
    social_score    REAL,
    safety_score    REAL,
    raw_total       REAL,
    flags           TEXT,
    final_score     REAL,
    recommended     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_scores_addr_ts ON scores(address, ts);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upsert_token(address, symbol=None, name=None, deployer=None,
                  deploy_ts=None, verified=None):
    now = int(time.time())
    with get_conn() as conn:
        row = conn.execute("SELECT address FROM tokens WHERE address=?", (address,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO tokens (address, symbol, name, deployer, deploy_ts, verified, first_seen) "
                "VALUES (?,?,?,?,?,?,?)",
                (address, symbol, name, deployer, deploy_ts, int(bool(verified)), now),
            )
        else:
            conn.execute(
                "UPDATE tokens SET symbol=COALESCE(?,symbol), name=COALESCE(?,name), "
                "deployer=COALESCE(?,deployer), deploy_ts=COALESCE(?,deploy_ts), "
                "verified=COALESCE(?,verified) WHERE address=?",
                (symbol, name, deployer, deploy_ts, int(bool(verified)) if verified is not None else None, address),
            )


def insert_snapshot(address, **metrics):
    now = int(time.time())
    cols = ["address", "ts"] + list(metrics.keys())
    vals = [address, now] + list(metrics.values())
    placeholders = ",".join("?" * len(cols))
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO snapshots ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )


def insert_social_snapshot(address, **metrics):
    now = int(time.time())
    cols = ["address", "ts"] + list(metrics.keys())
    vals = [address, now] + list(metrics.values())
    placeholders = ",".join("?" * len(cols))
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO social_snapshots ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )


def get_snapshots_since(address, since_ts):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE address=? AND ts>=? ORDER BY ts ASC",
            (address, since_ts),
        ).fetchall()
        return [dict(r) for r in rows]


def get_social_since(address, since_ts):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM social_snapshots WHERE address=? AND ts>=? ORDER BY ts ASC",
            (address, since_ts),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_score(address, breakdown, final_score, flags, recommended):
    now = int(time.time())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO scores (address, ts, liquidity_score, holder_score, social_score, "
            "safety_score, raw_total, flags, final_score, recommended) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                address, now,
                breakdown["liquidity"], breakdown["holders"],
                breakdown["social"], breakdown["safety"],
                breakdown["raw_total"], ",".join(flags), final_score,
                int(recommended),
            ),
        )


def all_tracked_tokens():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tokens").fetchall()
        return [dict(r) for r in rows]
