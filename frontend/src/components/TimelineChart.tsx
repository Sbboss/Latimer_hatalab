import { useId } from "react";

import type { TimelinePoint } from "../lib/types";

type Props = {
  data: TimelinePoint[];
  height?: number;
  showAxis?: boolean;
  dark?: boolean;
  responseLabel?: string | null;
};

const W = 600;

function buildSmoothPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) {
    const { x, y } = points[0];
    return `M ${x} ${y}`;
  }
  const d: string[] = [`M ${points[0].x} ${points[0].y}`];
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(points.length - 1, i + 2)];

    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;

    d.push(`C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`);
  }
  return d.join(" ");
}

export function TimelineChart({
  data,
  height = 140,
  showAxis = true,
  dark = false,
  responseLabel,
}: Props) {
  if (!data.length) return null;
  const gradientIdBase = useId().replace(/:/g, "-");
  const lightFillId = `${gradientIdBase}-timeline-fill`;
  const darkFillId = `${gradientIdBase}-timeline-fill-dark`;
  const activeFillId = dark ? darkFillId : lightFillId;

  const padX = 8;
  const padTop = 14;
  const padBottom = showAxis ? 22 : 8;

  const ys = data.map((d) => d.support);
  const xs = data.map((d) => d.year);
  const minY = Math.max(0, Math.min(...ys) - 8);
  const maxY = Math.min(100, Math.max(...ys) + 8);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);

  const xFor = (year: number) =>
    padX + ((year - minX) / Math.max(1, maxX - minX)) * (W - padX * 2);
  const yFor = (v: number) =>
    padTop +
    ((maxY - v) / Math.max(1, maxY - minY)) * (height - padTop - padBottom);

  const points = data.map((p) => ({ x: xFor(p.year), y: yFor(p.support) }));
  const linePath = buildSmoothPath(points);
  const last = points[points.length - 1];
  const first = points[0];
  const firstValue = data[0].support;
  const lastValue = data[data.length - 1].support;
  const change = lastValue - firstValue;
  const areaPath = `${linePath} L ${last.x} ${height - padBottom} L ${first.x} ${
    height - padBottom
  } Z`;

  return (
    <div className={`timeline-wrap${dark ? " timeline-wrap-dark" : ""}`}>
      <div className="timeline-summary">
        <span className="timeline-response-label">{responseLabel || "Selected response"}</span>
        <div className="timeline-stats">
          <span><strong>{lastValue.toFixed(1)}%</strong> latest</span>
          <span><strong>{change >= 0 ? "+" : ""}{change.toFixed(1)} pts</strong> since {data[0].year}</span>
        </div>
      </div>
      <svg
      className="timeline"
      viewBox={`0 0 ${W} ${height}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={`Observed response share over time: ${responseLabel || "selected response"}`}
    >
      <defs>
        <linearGradient id={lightFillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#B56A42" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#B56A42" stopOpacity="0" />
        </linearGradient>
        <linearGradient id={darkFillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#D4A373" stopOpacity="0.32" />
          <stop offset="100%" stopColor="#D4A373" stopOpacity="0" />
        </linearGradient>
      </defs>

      <g className="timeline-grid">
        {[0.25, 0.5, 0.75].map((t) => {
          const y = padTop + t * (height - padTop - padBottom);
          return <line key={t} x1={padX} x2={W - padX} y1={y} y2={y} />;
        })}
      </g>

      <path
        d={areaPath}
        className="timeline-area"
        style={{ fill: `url(#${activeFillId})` }}
      />
      <path d={linePath} className="timeline-line" />

      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3.6} className="timeline-dot" />
      ))}

      {showAxis && (
        <g className="timeline-axis">
          <text x={padX} y={height - 4} textAnchor="start">
            {minX}
          </text>
          <text x={W - padX} y={height - 4} textAnchor="end">
            {maxX}
          </text>
          <text
            x={W / 2}
            y={height - 4}
            textAnchor="middle"
          >
            {data[data.length - 1].support}% in {data[data.length - 1].year}
          </text>
        </g>
      )}
      </svg>
    </div>
  );
}
