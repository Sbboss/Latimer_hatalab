type Props = {
  waves?: string[];
  countryCount?: number | null;
  dark?: boolean;
  responseOptionCount?: number;
};

export function CoverageChart({ waves = [], countryCount, dark = false, responseOptionCount = 0 }: Props) {
  const displayWaves = waves.filter(Boolean);
  const pointCount = Math.max(displayWaves.length, 1);
  const startX = 24;
  const endX = 336;
  const pointX = (index: number) =>
    pointCount === 1
      ? (startX + endX) / 2
      : startX + (index / (pointCount - 1)) * (endX - startX);
  const waveLabel = `${displayWaves.length} survey wave${
    displayWaves.length === 1 ? "" : "s"
  }`;
  const countryLabel =
    typeof countryCount === "number"
      ? `${countryCount} countr${countryCount === 1 ? "y" : "ies"}`
      : "Country count unavailable";
  const spanLabel = displayWaves.length > 1
    ? `${displayWaves[0]}–${displayWaves[displayWaves.length - 1]}`
    : displayWaves[0] || "Year unavailable";
  const optionLabel = responseOptionCount
    ? `${responseOptionCount} response categories`
    : "Response categories unavailable";
  const ariaLabel = `Research scope: ${waveLabel}, ${countryLabel}, ${optionLabel}.`;

  return (
    <div
      className={`coverage-chart${dark ? " coverage-chart-dark" : ""}`}
      role="img"
      aria-label={ariaLabel}
    >
      <div className="coverage-chart-head">
        <strong>Research scope</strong>
        <span>Question metadata</span>
      </div>
      <svg viewBox="0 0 360 78" aria-hidden>
        <line x1={startX} x2={endX} y1="32" y2="32" />
        {(displayWaves.length ? displayWaves : ["Coverage"]).map((wave, index) => {
          const x = pointX(index);
          const showLabel =
            displayWaves.length <= 5 ||
            index === 0 ||
            index === displayWaves.length - 1;
          return (
            <g key={`${wave}-${index}`}>
              <circle cx={x} cy="32" r="5" />
              {showLabel && (
                <text x={x} y="61" textAnchor="middle">
                  {wave}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="coverage-chart-foot">
        <span>{spanLabel}</span>
        <span>{countryLabel}</span>
      </div>
      <div className="coverage-chart-stats">
        <span><strong>{displayWaves.length}</strong> waves</span>
        <span><strong>{typeof countryCount === "number" ? countryCount : "—"}</strong> countries</span>
        <span><strong>{responseOptionCount || "—"}</strong> response categories</span>
      </div>
    </div>
  );
}
