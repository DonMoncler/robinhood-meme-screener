import { useEffect, useState } from "react";
import Link from "next/link";

const REFRESH_MS = 120000;

function fmtUsd(n) {
  if (n === null || n === undefined) return "--";
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`;
  return `$${n.toFixed(2)}`;
}

function Row({ c }) {
  return (
    <tr>
      <td className="symbol-cell">
        <span className="symbol">{c.symbol}</span>
        <span className="address">{c.address ? `${c.address.slice(0, 6)}...${c.address.slice(-4)}` : ""}</span>
      </td>
      <td>{fmtUsd(c.market_cap_usd)}</td>
      <td>{fmtUsd(c.liquidity_usd)}</td>
      <td>{fmtUsd(c.volume_24h_usd)}</td>
      <td className="buzz-cell">
        <span className="mentions">{c.twitter_mentions} mentions</span>
        <span className="authors">{c.twitter_distinct_authors} accounts</span>
      </td>
      <td>
        {c.dexscreener_url ? (
          <a href={c.dexscreener_url} target="_blank" rel="noreferrer" className="chart-link">
            Chart &rarr;
          </a>
        ) : (
          "--"
        )}
      </td>
    </tr>
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

  return (
    <div className="container">
      <header>
        <h1>Twitter Gems -- Under ${(data.market_cap_ceiling || 500000).toLocaleString()} Market Cap</h1>
        <p className="subtitle">
          Personal research tool -- not financial advice. Low-cap Robinhood Chain coins with the loudest X activity.
        </p>
        <p className="nav-link"><Link href="/">&larr; Back to main screener</Link></p>
        {data.last_updated && (
          <p className="last-updated">
            Data refreshed: {new Date(data.last_updated * 1000).toLocaleString()}
          </p>
        )}
      </header>

      {loading ? (
        <p>Loading...</p>
      ) : data.coins.length === 0 ? (
        <p className="empty">
          No matches yet. Either the scan hasn't run, or nothing under the market cap ceiling has enough X buzz right now.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Token</th>
              <th>Market Cap</th>
              <th>Liquidity</th>
              <th>24h Volume</th>
              <th>Twitter Buzz</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.coins.map((c) => (
              <Row key={c.symbol + (c.address || "")} c={c} />
            ))}
          </tbody>
        </table>
      )}

      <footer>
        <p>Ranked by mention count x distinct posting accounts (not repeat posts from the same account). Refreshes hourly.</p>
      </footer>
    </div>
  );
}
