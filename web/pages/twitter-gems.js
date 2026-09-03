import { useEffect, useState } from "react";
import Nav from "../components/Nav";

const REFRESH_MS = 120000;

function fmtUsd(n) {
  if (n === null || n === undefined) return "--";
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`;
  return `$${n.toFixed(2)}`;
}

function buzzPct(c, maxMentions) {
  if (!maxMentions) return 0;
  return Math.min(100, Math.round((c.twitter_mentions / maxMentions) * 100));
}

function GemCard({ c, maxMentions }) {
  const pct = buzzPct(c, maxMentions);
  const url = c.dexscreener_url || (c.address ? `https://dexscreener.com/robinhood/${c.address}` : null);

  function openChart() {
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <div className={url ? "gem-card gem-clickable" : "gem-card"} onClick={openChart} title={url ? "Open chart on DexScreener" : undefined}>
      <div className="gem-header">
        <div>
          <div className="gem-symbol">{c.symbol}</div>
          {c.address && (
            <div className="gem-address">{c.address.slice(0, 6)}...{c.address.slice(-4)}</div>
          )}
        </div>
        {url && <span className="chart-link">Chart &#8599;</span>}
      </div>

      <div className="gem-stats">
        <div className="gem-stat">
          <span className="gem-stat-label">Market Cap</span>
          <span className="gem-stat-value">{fmtUsd(c.market_cap_usd)}</span>
        </div>
        <div className="gem-stat">
          <span className="gem-stat-label">Liquidity</span>
          <span className="gem-stat-value">{fmtUsd(c.liquidity_usd)}</span>
        </div>
        <div className="gem-stat">
          <span className="gem-stat-label">24h Volume</span>
          <span className="gem-stat-value">{fmtUsd(c.volume_24h_usd)}</span>
        </div>
      </div>

      <div className="buzz-section">
        <div className="buzz-bar-wrap">
          <div className="buzz-bar" style={{ width: `${pct}%` }} />
        </div>
        <div className="buzz-labels">
          <span>{c.twitter_mentions} mentions</span>
          <span>{c.twitter_distinct_authors} accounts</span>
        </div>
      </div>
    </div>
  );
}

export default function TwitterGems() {
  const [data, setData] = useState({ coins: [], last_updated: null, market_cap_ceiling: 500000 });
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const r = await fetch("/api/twitter-gems");
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

  const coins = data.coins || [];
  const maxMentions = coins.length ? Math.max(...coins.map((c) => c.twitter_mentions)) : 0;

  return (
    <div className="page">
      <Nav />
      <div className="container">
        <header>
          <h1>Twitter Gems</h1>
          <p className="subtitle">
            Under ${(data.market_cap_ceiling || 500000).toLocaleString()} market cap, ranked by X buzz. Click a card to open its chart.
          </p>
          {data.last_updated && (
            <p className="last-updated">
              Data refreshed: {new Date(data.last_updated * 1000).toLocaleString()}
            </p>
          )}
        </header>

        {loading ? (
          <p className="loading">Loading...</p>
        ) : coins.length === 0 ? (
          <p className="empty">
            No matches yet. Either the scan hasn't run, or nothing under the market cap ceiling has enough X buzz right now.
          </p>
        ) : (
          <div className="gem-grid">
            {coins.map((c) => (
              <GemCard key={c.symbol + (c.address || "")} c={c} maxMentions={maxMentions} />
            ))}
          </div>
        )}

        <footer>
          <p>Ranked by mention count x distinct posting accounts (not repeat posts from the same account). Refreshes hourly.</p>
        </footer>
      </div>
    </div>
  );
}
