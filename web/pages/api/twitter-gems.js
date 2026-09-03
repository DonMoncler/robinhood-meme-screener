const GITHUB_USER = process.env.GITHUB_USER || "DonMoncler";
const GITHUB_REPO = process.env.GITHUB_REPO || "robinhood-meme-screener";
const BRANCH = process.env.GITHUB_BRANCH || "main";

export default async function handler(req, res) {
  const url = `https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${BRANCH}/data/twitter_gems.json?t=${Date.now()}`;
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) {
      res.status(200).json({ coins: [], last_updated: null, market_cap_ceiling: 500000, error: "no data yet" });
      return;
    }
    const data = await r.json();
    res.setHeader("Cache-Control", "no-store");
    res.status(200).json(data);
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
}
