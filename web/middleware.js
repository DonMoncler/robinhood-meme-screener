const USER = process.env.SITE_USER || "london";
const PASS = process.env.SITE_PASSWORD || "RHscreen2026!";

export function middleware(req) {
  const auth = req.headers.get("authorization");
  if (auth) {
    const [, encoded] = auth.split(" ");
    const decoded = atob(encoded);
    const [user, pass] = decoded.split(":");
    if (user === USER && pass === PASS) {
      return;
    }
  }
  return new Response("Auth required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Robinhood Meme Screener"' },
  });
}

export const config = {
  matcher: "/((?!_next/static|_next/image|favicon.ico).*)",
};
