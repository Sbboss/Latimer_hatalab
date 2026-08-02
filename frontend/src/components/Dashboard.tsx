import type { AnalysisResult } from "../lib/types";

type Props = {
  analysis: AnalysisResult;
  apiSource: "live" | "mock" | "unknown";
};

export function Dashboard({ analysis, apiSource }: Props) {
  const pct = Math.round(analysis.overallScore * 100);
  const conf = Math.round(analysis.confidence * 100);
  const dimensionsCount = new Set(
    analysis.highlights.map((h) => h.category)
  ).size;
  const status = analysis.highlights.length
    ? `${analysis.highlights.length} signals detected`
    : "No signals detected";

  return (
    <div className="dashboard" aria-live="polite">
      <div className="dash-section">
        <span className="dash-label">Bias Signal Strength</span>
        <div className="dash-score">
          <span className="dash-score-num">{analysis.overallScore.toFixed(2)}</span>
          <span className="dash-score-den">/ 1.00</span>
        </div>
        <div className="dash-bar">
          <div className="dash-bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            marginTop: 4,
            fontSize: 13,
            color: "var(--ink-2)",
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--accent)",
              display: "inline-block",
            }}
          />
          {analysis.signalLabel}
          <span style={{ color: "var(--ink-4)", marginLeft: 4 }}>
            · this is a signal strength, not a verdict
          </span>
        </span>
      </div>

      <div className="dash-stats">
        <div className="dash-stat">
          <div className="dash-stat-label">Confidence</div>
          <div className="dash-stat-value">{conf}%</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-label">Bias dimensions</div>
          <div className="dash-stat-value">{dimensionsCount}</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-label">Highlighted signals</div>
          <div className="dash-stat-value">{analysis.highlights.length}</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-label">Suggested rewrites</div>
          <div className="dash-stat-value">{analysis.highlights.length}</div>
        </div>
      </div>

      <div
        style={{
          marginTop: -8,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--ink-3)",
        }}
      >
        <span>{status}</span>
        <span>
          {apiSource === "live"
            ? "Source · Live"
            : apiSource === "mock"
            ? "Source · Curated demo"
            : "Source · Pending"}
        </span>
      </div>
    </div>
  );
}
