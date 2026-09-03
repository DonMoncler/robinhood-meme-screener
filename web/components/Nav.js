import Link from "next/link";
import { useRouter } from "next/router";

export default function Nav() {
  const router = useRouter();

  return (
    <nav className="topnav">
      <div className="brand">
        <span className="brand-orb" />
        <span className="brand-text">
          RH<span className="brand-accent">SCAN</span>
        </span>
      </div>
      <div className="nav-tabs">
        <Link href="/" className={router.pathname === "/" ? "tab active" : "tab"}>
          Screener
        </Link>
        <Link href="/twitter-gems" className={router.pathname === "/twitter-gems" ? "tab active" : "tab"}>
          Twitter Gems
        </Link>
      </div>
    </nav>
  );
}
