type Props = {
  waves?: string[];
  countryCount?: number | null;
  dark?: boolean;
  responseOptionCount?: number;
  responseOptions?: string[];
};

export function CoverageChart({
  waves = [],
  countryCount,
  dark = false,
  responseOptionCount = 0,
  responseOptions = [],
}: Props) {
  const displayWaves = waves.filter(Boolean);
  const spanLabel = displayWaves.length > 1
    ? `${displayWaves[0]}–${displayWaves[displayWaves.length - 1]}`
    : displayWaves[0] || "Year unavailable";
  const compactOptions = responseOptions
    .map((option) => option.trim())
    .filter(Boolean)
    .slice(0, 8);
  const showsScale = responseOptionCount > 0 && responseOptionCount <= 8 && compactOptions.length > 0;

  return (
    <div
      className={`measurement-profile${dark ? " measurement-profile-dark" : ""}`}
      aria-label="Survey question design"
    >
      <div className="measurement-profile-head">
        <strong>How this question was measured</strong>
        <span>{spanLabel}</span>
      </div>
      <div className="measurement-facts">
        <div><span>Survey waves</span><strong>{displayWaves.length || "—"}</strong></div>
        <div><span>Countries</span><strong>{typeof countryCount === "number" ? countryCount : "—"}</strong></div>
      </div>
      <div className="measurement-scale">
        <span>Response scale</span>
        {showsScale ? (
          <ol>
            {compactOptions.map((option, index) => <li key={`${option}-${index}`}>{option}</li>)}
          </ol>
        ) : (
          <p>
            {responseOptionCount > 8
              ? `${responseOptionCount} coded response categories`
              : "Response labels unavailable in this record"}
          </p>
        )}
      </div>
    </div>
  );
}
