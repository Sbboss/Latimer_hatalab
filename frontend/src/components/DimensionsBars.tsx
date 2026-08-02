import type { Dimension } from "../lib/types";

type Props = {
  dimensions: Dimension[];
};

export function DimensionsBars({ dimensions }: Props) {
  if (!dimensions.length) return null;
  const sorted = [...dimensions].sort((a, b) => b.score - a.score);
  const top = sorted[0];

  return (
    <div className="dims">
      {sorted.map((d) => {
        const pct = Math.round(d.score * 100);
        const isPrimary = d.label === top.label;
        return (
          <div className={`dim ${isPrimary ? "is-primary" : ""}`} key={d.label}>
            <span className="dim-name">{d.label}</span>
            <span className="dim-value">{d.score.toFixed(2)}</span>
            <div className="dim-track">
              <div className="dim-fill" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
