import type { Highlight, ModelAnalysis } from "../lib/types";
import { DimensionsBars } from "./DimensionsBars";
import { TimelineChart } from "./TimelineChart";

type Props = {
  highlight: Highlight | null;
  models: ModelAnalysis[];
  activeModelIndex: number;
  onModelSelect: (index: number) => void;
};

export function Cockpit({ highlight, models, activeModelIndex, onModelSelect }: Props) {
  if (!highlight) {
    return (
      <section className="cockpit" id="cockpit" aria-label="Bias Intelligence Cockpit">
        <div className="cockpit-head">
          <div>
            <div className="cockpit-eyebrow">Bias Intelligence Cockpit</div>
            <h2 className="cockpit-phrase">No bias signals detected.</h2>
            <p
              style={{
                marginTop: 12,
                color: "rgba(247, 240, 230, 0.7)",
                fontSize: 16,
                maxWidth: 560,
              }}
            >
              Try editing the text on the left to include phrases like
              “surprisingly articulate”, “strong cultural fit”, or “not quite
              leadership material” to see the cockpit come alive.
            </p>
          </div>
        </div>
      </section>
    );
  }

  // Only show models that actually detected this phrase
  const modelsWithPhrase = models
    .map((m, idx) => ({ model: m, index: idx }))
    .filter(({ model }) =>
      model.result.highlights?.some((h) =>
        h.phrase?.toLowerCase() === highlight.phrase?.toLowerCase()
      )
    );

  const extractQuestionText = (content: string) => {
    const text = content?.toString() ?? "";
    const lines = text
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (!lines.length) return "";
    let firstLine = lines[0];
    if (firstLine.toLowerCase().startsWith("question:")) {
      firstLine = firstLine.slice(9).trim();
    }
    return firstLine;
  };

  return (
    <section className="cockpit" id="cockpit" aria-label="Bias Intelligence Cockpit">
      <div className="cockpit-head">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="cockpit-eyebrow">Detected bias signal</div>
          <h2 className="cockpit-phrase">
            “<em>{highlight.phrase}</em>”
          </h2>

          <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
            {modelsWithPhrase.map(({ model: m, index: i }) => (
              <button
                key={m.model}
                onClick={() => onModelSelect(i)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 999,
                  border: i === activeModelIndex ? "1px solid var(--accent-warm)" : "1px solid rgba(255,255,255,0.15)",
                  background: i === activeModelIndex ? "rgba(255,255,255,0.08)" : "transparent",
                  color: "var(--fg)",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                {m.model}
              </button>
            ))}
          </div>
          <div className="cockpit-meta">
            <span className="chip chip-ink">
              <span className="chip-dot" style={{ color: "var(--accent-warm)" }} />
              {highlight.category}
            </span>
            <a href="#evidence" className="chip chip-ink chip-link">
              {highlight.evidence.length} grounded survey question
              {highlight.evidence.length === 1 ? "" : "s"}
            </a>
          </div>
        </div>

        <div className="cockpit-strength">
          <div className="cockpit-strength-num">
            {highlight.score.toFixed(2)}
          </div>
          <div className="cockpit-strength-label">Bias signal strength</div>
        </div>
      </div>

      <div className="cockpit-body">
        <div className="cockpit-col">
          <div className="cockpit-block">
            <div className="cockpit-h">What we noticed</div>
            <p className="cockpit-text">{highlight.explanation}</p>
          </div>

          <div className="cockpit-block">
            <div className="cockpit-h">Pause and reflect</div>
            <p className="cockpit-text">
              {highlight.reflectionQuestion ??
                "What assumption about this person or group might this wording invite?"}
            </p>
          </div>

          <div className="cockpit-block">
            <div className="cockpit-h">Suggested rewrite</div>
            <div className="rewrite-row">
              <div className="rewrite-card original">
                <div className="rewrite-label">Original</div>
                <div className="rewrite-text">“{highlight.phrase}”</div>
              </div>
              <div className="rewrite-card replacement">
                <div className="rewrite-label">Suggested replacement</div>
                <div className="rewrite-text">“{highlight.replacement}”</div>
              </div>
            </div>
            <p className="rewrite-why">
              <strong style={{ color: "var(--accent-warm)", fontWeight: 500 }}>
                Why this helps —{" "}
              </strong>
              {highlight.rewriteReason}
            </p>
          </div>
        </div>

        <div className="cockpit-col">
          <div className="cockpit-block">
            <div className="cockpit-h">Bias dimensions</div>
            <DimensionsBars dimensions={highlight.dimensions} />
          </div>

          <div className="cockpit-block" id="evidence">
            <div className="cockpit-h">Grounded survey questions</div>
            {!highlight.evidence.length && (
              <p className="cockpit-text" style={{ marginTop: 12 }}>
                No retrieved survey question directly matches this bias category.
                The system is leaving the evidence area empty instead of showing a
                tangential source.
              </p>
            )}
            {highlight.evidence.map((evidence, index) => (
              <article
                key={evidence.recordId ?? `${evidence.question}-${index}`}
                style={{
                  marginTop: 16,
                  paddingTop: index ? 18 : 0,
                  borderTop: index ? "1px solid rgba(247, 240, 230, 0.16)" : "none",
                }}
              >
                <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                  <span className="chip chip-ink">
                    {evidence.survey ?? "Survey"}
                  </span>
                  {evidence.module && (
                    <span className="chip chip-ink">{evidence.module}</span>
                  )}
                  {evidence.uncertain && (
                    <span className="chip chip-ink">Annotation uncertain</span>
                  )}
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: 19,
                    lineHeight: 1.45,
                    letterSpacing: "-0.012em",
                    marginTop: 12,
                    color: "var(--bg)",
                    fontWeight: 500,
                  }}
                >
                  “{extractQuestionText(evidence.question)}”
                </p>
                <p
                  style={{
                    marginTop: 9,
                    fontSize: 13,
                    color: "rgba(247, 240, 230, 0.72)",
                    lineHeight: 1.5,
                  }}
                >
                  {evidence.availableWaves?.length
                    ? `Waves: ${evidence.availableWaves.join(", ")}`
                    : "Waves not supplied"}
                  {typeof evidence.countryCount === "number"
                    ? ` · ${evidence.countryCount} countr${evidence.countryCount === 1 ? "y" : "ies"}`
                    : ""}
                  {evidence.sourceDataset ? ` · ${evidence.sourceDataset}` : ""}
                </p>
                {evidence.timeline.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <TimelineChart data={evidence.timeline} height={140} />
                  </div>
                )}
                <p
                  style={{
                    marginTop: 14,
                    fontSize: 14,
                    color: "rgba(247, 240, 230, 0.78)",
                    lineHeight: 1.55,
                  }}
                >
                  {evidence.insight}
                </p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
