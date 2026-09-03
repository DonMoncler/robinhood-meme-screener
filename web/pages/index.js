import { useEffect, useMemo, useState } from "react";
import Nav from "../components/Nav";

const REFRESH_MS = 60000;

function scoreColor(score) {
  if (score >= 60) return "#3fe08a";
  if (score >= 45) return "#f5c542";
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
  return (
    <tr className={capped ? "row-capped" : ""}>
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
    </tr>
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
            Personal research tool -- not financial advice. Chain ID 4663.
          </p>
          {data.last_updated && (
            <p className="last-updated">
              Data refreshed: {new Date(data.last_updated * 1000).toLocaleString()}
            </p>
          )}
        </header>

        {!loading && tokens.length > 0 && (
          <div className="stat-row">
            <StatCard label="Tokens tracked" value={tokens.length} />
            <StatCard label="Recommended" value={recommendedCount} accent="#3fe08a" />
            <StatCard label="Top score" value={`${topScore}/90`} accent="#58a6ff" />
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
          <p>2+ manipulation flags cap a token's score at 40/90 and exclude it from "recommended." Click column headers to sort.</p>
        </footer>
      </div>
    </div>
  );
}
