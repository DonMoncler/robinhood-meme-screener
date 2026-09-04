export default function HoloCore({ label = "LIVE FEED", value }) {
  return (
    <div className="holo-core-wrap">
      <div className="holo-core">
        <div className="ring ring-1" />
        <div className="ring ring-2" />
        <div className="ring ring-3" />
        <div className="core-glow" />
        <div className="core-dot" />
      </div>
      <div className="holo-core-label">
        <span className="holo-core-tag">{label}</span>
        <span className="holo-core-sub">Updating...</span>
        {value !== undefined && <span className="holo-core-value">{value}</span>}
      </div>
      <div className="holo-core-beam" />
    </div>
  );
}
