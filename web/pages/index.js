import { useEffect, useState } from "react";

const REFRESH_MS = 60000;

function scoreColor(score) {
  if (score >= 60) return "#2ecc71";
  if (score >= 45) return "#f1c40f";
  return "#e74c3c";
}

function FlagBadge({ flag }) {
  return <span className="flag-badge">{flag.replaceAll("_", " ")}</span>;
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
            style={{ width: `${(t.final_score / 90) * 100}%`, background: scoreColor(t.final_score) }}
          />
          <span className="score-label">{t.final_score}/90</span>
        </div>
      </td>
      <td>{t.recommended ? <span className="rec-yes">YES</span> : <span className="rec-no">no</span>}</td>
      <td>
        {flags.length === 0 ? (
          <span className="flag-none">clean</span>
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

  const tokens = (data.tokens || []).slice().sort((a, b) => b.final_score - a.final_score);

  return (
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

      {loading ? (
        <p>Loading...</p>
      ) : tokens.length === 0 ? (
        <p className="empty">
          No data yet. Once the GitHub Action runs its first poll cycle, tokens will show up here.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Token</th>
              <th>Score</th>
              <th>Recommended</th>
              <th>Flags</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {tokens.map((t) => (
              <TokenRow key={t.address} t={t} />
            ))}
          </tbody>
        </table>
      )}

      <footer>
        <p>2+ manipulation flags cap a token's score at 40/90 and exclude it from "recommended."</p>
      </footer>
    </div>
  );
}
