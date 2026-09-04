import { useEffect, useMemo, useState } from "react";
import Nav from "../components/Nav";
import HoloCore from "../components/HoloCore";

const REFRESH_MS = 60000;

function scoreColor(score) {
  if (score >= 60) return "#6fe9ff";
  if (score >= 45) return "#8ff3ff";
  return "#ff5c6c";
}

function StatCard({ label, value, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={accent ? { color: accent } : undefined}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function FlagBadge({ flag }) {
  return <span className="flag-badge">{flag.replaceAll("_", " ")}</span>;
}

function SortArrow({ active, dir }) {
  if (!active) return <span className="sort-arrow idle">&#8597;</span>;
  return <span className="sort-arrow active">{dir === "asc" ? "\u2191" : "\u2193"}</span>;
}

function TokenRow({ t }) {
  const flags = t.flags ? t.flags.split(",").filter(Boolean) : [];
  const capped = flags.length >= 2;
  const chartUrl = `https://dexscreener.com/robinhood/${t.address}`;

  function openChart() {
    window.open(chartUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <tr
      className={capped ? "row-capped row-clickable" : "row-clickable"}
      onClick={openChart}
      title="Open chart on DexScreener"
    >
      <td className="symbol-cell">
        <span className="symbol">{t.symbol || "?"}</span>
        <span className="address">{t.address.slice(0, 6)}...{t.address.slice(-4)}</span>
      </td>
      <td>
        <div className="score-bar-wrap">
          <div
            className="score-bar"
            style={{ width: `${(t.final_score / 90) * 100}%`, background: scoreColor(t.final_score), boxShadow: `0 0 10px ${scoreColor(t.final_score)}66` }}
          />
          <span className="score-label">{t.final_score}/90</span>
        </div>
      </td>
      <td>{t.recommended ? <span className="rec-yes">&#10003; YES</span> : <span className="rec-no">no</span>}</td>
      <td>
        {flags.length === 0 ? (
          <span className="flag-none">&#10003; clean</span>
        ) : (
          flags.map((f) => <FlagBadge key={f} flag={f} />)
        )}
      </td>
      <td className="ts-cell">{new Date(t.ts * 1000).toLocaleTimeString()}</td>
      <td className="row-link-cell">
        <span className="row-link">Chart &#8599;</span>
      </td>
    </tr>
  );
}

function FeedPanel({ tokens }) {
  const feed = tokens.slice(0, 7);
  return (
    <div className="dash-panel feed-panel">
      <div className="dash-panel-head">
        <span className="dash-panel-title">New Token Feed</span>
        <span className="live-dot"><span className="live-pulse" />LIVE</span>
      </div>
      <div className="feed-cols">
        <span>TIME</span>
        <span>TOKEN</span>
        <span>ADDRESS</span>
      </div>
      <div className="feed-rows">
        {feed.map((t) => (
          <div
            key={t.address}
            className="feed-row"
            onClick={() => window.open(`https://dexscreener.com/robinhood/${t.address}`, "_blank", "noopener,noreferrer")}
          >
            <span className="feed-time">{new Date(t.ts * 1000).toLocaleTimeString()}</span>
            <span className="feed-symbol">{t.symbol || "?"}</span>
            <span className="feed-address">{t.address.slice(0, 6)}...{t.address.slice(-4)}</span>
          </div>
        ))}
        {feed.length === 0 && <div className="feed-empty">No tokens yet</div>}
      </div>
      <div className="dash-panel-foot">
        <span>TOTAL TODAY</span>
        <span className="dash-panel-foot-value">{tokens.length}</span>
      </div>
    </div>
  );
}

function RecommendedPanel({ tokens }) {
  const ranked = tokens
    .slice()
    .sort((a, b) => b.final_score - a.final_score)
    .slice(0, 7);
  const maxScore = ranked.length ? ranked[0].final_score : 90;

  return (
    <div className="dash-panel liq-panel">
      <div className="dash-panel-head">
        <span className="dash-panel-title">Top Recommended Coins</span>
        <span className="badge-tag">ROBINHOOD CHAIN</span>
      </div>
      <div className="rec-list">
        {ranked.map((t) => (
          <div
            key={t.address}
            className="rec-row"
            onClick={() => window.open(`https://dexscreener.com/robinhood/${t.address}`, "_blank", "noopener,noreferrer")}
          >
            <span className="rec-row-symbol">{t.symbol || "?"}</span>
            <div className="rec-row-bar-wrap">
              <div
                className="rec-row-bar"
                style={{ width: `${(t.final_score / 90) * 100}%` }}
              />
            </div>
            <span className="rec-row-score">{t.final_score}</span>
          </div>
        ))}
        {ranked.length === 0 && <div className="feed-empty">No tokens yet</div>}
      </div>
      <div className="dash-panel-foot">
        <span>TOP SCORE</span>
        <span className="dash-panel-foot-value">{maxScore}/90</span>
      </div>
    </div>
  );
}

function WalletPanel() {
  const rows = new Array(6).fill(null);
  return (
    <div className="dash-panel wallet-panel">
      <div className="dash-panel-head">
        <span className="dash-panel-title">Wallet Tracking</span>
        <span className="badge-tag">TOP HOLDERS</span>
      </div>
      <div className="wallet-cols">
        <span>WALLET</span>
        <span>HOLDING %</span>
      </div>
      <div className="wallet-rows">
        {rows.map((_, i) => (
          <div className="wallet-row" key={i}>
            <span className="wallet-addr"><span className="wallet-icon">&#9679;</span>0x----...----</span>
            <span className="wallet-pct">--%</span>
          </div>
        ))}
      </div>
      <div className="dash-panel-foot">
        <span>PER-WALLET DATA</span>
        <span className="dash-panel-foot-value">pending</span>
      </div>
    </div>
  );
}

function RiskPanel({ token }) {
  if (!token) {
    return (
      <div className="dash-panel risk-panel">
        <div className="dash-panel-head"><span className="dash-panel-title">Risk Analysis</span></div>
        <div className="feed-empty">No token selected yet.</div>
      </div>
    );
  }
  const flags = token.flags ? token.flags.split(",").filter(Boolean) : [];
  const riskPct = Math.max(0, Math.min(100, Math.round(100 - (token.final_score / 90) * 100)));
  const riskLabel = riskPct >= 60 ? "HIGH RISK" : riskPct >= 30 ? "ELEVATED" : "LOW RISK";
  const checks = [
    ["one_sided_buying", "One-Sided Buying"],
    ["social_spike_no_holders", "Social Spike"],
    ["extreme_volume_ratio", "Volume Ratio"],
    ["high_concentration", "High Concentration"],
  ];

  return (
    <div className="dash-panel risk-panel">
      <div className="dash-panel-head">
        <span className="dash-panel-title">Risk Analysis</span>
        <span className="badge-tag">{token.symbol || "?"}</span>
      </div>
      <div className="gauge-wrap">
        <span className="gauge-label">RISK SCORE</span>
        <div className="gauge">
          <svg viewBox="0 0 120 66">
            <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke="rgba(111,233,255,0.12)" strokeWidth="9" />
            <path
              d="M10,60 A50,50 0 0,1 110,60"
              fill="none"
              stroke="#6fe9ff"
              strokeWidth="9"
              strokeDasharray={`${(riskPct / 100) * 157} 157`}
              style={{ filter: "drop-shadow(0 0 6px #6fe9ffaa)" }}
            />
          </svg>
          <div className="gauge-value">{riskPct}</div>
        </div>
        <span className="gauge-tag">{riskLabel}</span>
      </div>
      <div className="risk-rows">
        {checks.map(([key, label]) => (
          <div className="risk-row" key={key}>
            <span>{label}</span>
            <span className={flags.includes(key) ? "risk-yes" : "risk-no"}>{flags.includes(key) ? "YES" : "NO"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [data, setData] = useState({ tokens: [], last_updated: null });
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState("final_score");
  const [sortDir, setSortDir] = useState("desc");

  async function load() {
    try {
      const r = await fetch("/api/data");
      const json = await r.json();
      setData(json);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const tokens = useMemo(() => {
    const list = (data.tokens || []).slice();
    list.sort((a, b) => {
      let av = a[sortKey];
      let bv = b[sortKey];
      if (sortKey === "symbol") {
        av = (av || "").toLowerCase();
        bv = (bv || "").toLowerCase();
      }
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [data.tokens, sortKey, sortDir]);

  const feedOrdered = useMemo(() => {
    return (data.tokens || []).slice().sort((a, b) => b.ts - a.ts);
  }, [data.tokens]);

  const topToken = tokens.length ? tokens[0] : null;

  const recommendedCount = tokens.filter((t) => t.recommended).length;
  const topScore = tokens.length ? Math.max(...tokens.map((t) => t.final_score)) : 0;
  const cleanCount = tokens.filter((t) => !t.flags).length;

  return (
    <div className="page">
      <Nav />
      <div className="container">
        <header>
          <h1>Robinhood Chain Meme Screener</h1>
          <p className="subtitle">
            Personal research tool -- not financial advice. Chain ID 4663. Click any row to open its chart.
          </p>
          {data.last_updated && (
            <p className="last-updated">
              Data refreshed: {new Date(data.last_updated * 1000).toLocaleString()}
            </p>
          )}
        </header>
      </div>

      {!loading && (
        <div className="dash-wrap">
          <div className="dash-grid">
            <FeedPanel tokens={feedOrdered} />
            <RecommendedPanel tokens={tokens} />
            <WalletPanel />
            <RiskPanel token={topToken} />
            <div className="dash-core">
              <HoloCore label="Live Token Activity" value={tokens.length} />
            </div>
          </div>
        </div>
      )}

      <div className="container">
        {!loading && tokens.length > 0 && (
          <div className="stat-row">
            <StatCard label="Tokens tracked" value={tokens.length} />
            <StatCard label="Recommended" value={recommendedCount} accent="#6fe9ff" />
            <StatCard label="Top score" value={`${topScore}/90`} accent="#6fe9ff" />
            <StatCard label="Clean (no flags)" value={cleanCount} />
          </div>
        )}

        {loading ? (
          <p className="loading">Loading...</p>
        ) : tokens.length === 0 ? (
          <p className="empty">
            No data yet. Once the GitHub Action runs its first poll cycle, tokens will show up here.
          </p>
        ) : (
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th onClick={() => toggleSort("symbol")} className="sortable">
                    Token <SortArrow active={sortKey === "symbol"} dir={sortDir} />
                  </th>
                  <th onClick={() => toggleSort("final_score")} className="sortable">
                    Score <SortArrow active={sortKey === "final_score"} dir={sortDir} />
                  </th>
                  <th onClick={() => toggleSort("recommended")} className="sortable">
                    Recommended <SortArrow active={sortKey === "recommended"} dir={sortDir} />
                  </th>
                  <th>Flags</th>
                  <th onClick={() => toggleSort("ts")} className="sortable">
                    Updated <SortArrow active={sortKey === "ts"} dir={sortDir} />
                  </th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tokens.map((t) => (
                  <TokenRow key={t.address} t={t} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <footer>
          <p>2+ manipulation flags cap a token's score at 40/90 and exclude it from "recommended." Click column headers to sort, click a row to open its chart.</p>
        </footer>
      </div>
    </div>
  );
}
