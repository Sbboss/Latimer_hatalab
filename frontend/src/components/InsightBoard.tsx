import type { Highlight, ModelAnalysis } from "../lib/types";
import { groupEvidenceBySurvey, SURVEY_ORDER } from "../lib/evidence";
import { CoverageChart } from "./CoverageChart";
import { DimensionsBars } from "./DimensionsBars";
import { SurveyQuestion } from "./SurveyQuestion";
import { TimelineChart } from "./TimelineChart";

type Props = {
  highlight: Highlight | null;
  models: ModelAnalysis[];
  activeModelIndex: number;
  onModelSelect: (index: number) => void;
};

export function InsightBoard({ highlight, models, activeModelIndex, onModelSelect }: Props) {
  if (!highlight) {
    return (
      <div
        className="insight-board"
        role="region"
        aria-labelledby="insight-board-title"
        aria-live="polite"
      >
        <div className="insight-board-head">
          <div>
            <div className="insight-board-eyebrow">Insight Board status</div>
            <h2 className="insight-board-phrase">No bias signals detected.</h2>
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
              leadership material” to populate the Insight Board.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show every model that returned a result, not just the ones that
  // flagged the exact same text as the currently active model. Each model
  // picks its own highlight boundaries (whole sentence vs. individual
  // clauses), and clicking a model button switches to that model's own
  // first highlight (see handleModelSelect in App.tsx), so there's no
  // reason to filter the switcher by phrase at all -- every model that
  // ran should always be selectable.
  const modelsWithPhrase = models
    .map((m, idx) => ({ model: m, index: idx }))
    .filter(({ model }) => (model.result.highlights?.length ?? 0) > 0);
  const evidenceBySurvey = groupEvidenceBySurvey(highlight.evidence, 1);
  const evidenceCount = SURVEY_ORDER.reduce(
    (count, survey) => count + evidenceBySurvey[survey].length,
    0
  );

  return (
    <div
      className="insight-board"
      role="region"
      aria-labelledby="insight-board-title"
      aria-live="polite"
    >
      <div className="insight-board-head">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="insight-board-eyebrow">Detected bias signal</div>
          <h2 className="insight-board-phrase">
            “<em>{highlight.phrase || "Selected signal"}</em>”
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
          <div className="insight-board-meta">
            <span className="chip chip-ink">
              <span className="chip-dot" style={{ color: "var(--accent-warm)" }} />
              {highlight.category}
            </span>
            <a href="#social-evidence" className="chip chip-ink chip-link">
              {evidenceCount} balanced survey question
              {evidenceCount === 1 ? "" : "s"}
            </a>
          </div>
        </div>

        <div className="insight-board-strength">
          <div className="insight-board-strength-num">
            {highlight.score.toFixed(2)}
          </div>
          <div className="insight-board-strength-label">Bias signal strength</div>
        </div>
      </div>

      <div className="insight-board-body">
        <div className="insight-board-col">
          <div className="insight-board-block">
            <div className="insight-board-h">What we noticed</div>
            <p className="insight-board-text">
              {highlight.explanation ||
                "The selected signal did not include an explanation. Try another model or analyze the text again."}
            </p>
          </div>

          <div className="insight-board-block">
            <div className="insight-board-h">Pause and reflect</div>
            <p className="insight-board-text">
              {highlight.reflectionQuestion?.trim() ||
                "What assumption about this person or group might this wording invite?"}
            </p>
          </div>

          <div className="insight-board-block">
            <div className="insight-board-h">Suggested rewrite</div>
            <div className="rewrite-row">
              <div className="rewrite-card original">
                <div className="rewrite-label">Original</div>
                <div className="rewrite-text">
                  “{highlight.phrase || "Selected signal"}”
                </div>
              </div>
              <div className="rewrite-card replacement">
                <div className="rewrite-label">Suggested replacement</div>
                <div className="rewrite-text">
                  “{highlight.replacement || "No replacement was returned."}”
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="insight-board-col">
          <div className="insight-board-block">
            <div className="insight-board-h">Bias dimensions</div>
            {highlight.dimensions.length ? (
              <DimensionsBars dimensions={highlight.dimensions} />
            ) : (
              <p className="insight-board-text">
                No dimension scores were returned for this signal.
              </p>
            )}
          </div>

          <div className="insight-board-block" id="insight-board-evidence">
            <div className="insight-board-h">
              Balanced survey evidence
            </div>
            {SURVEY_ORDER.map((survey, index) => {
              const evidence = evidenceBySurvey[survey][0];
              return (
                <article
                  key={evidence?.recordId ?? `${survey}-missing`}
                  style={{
                    marginTop: 16,
                    paddingTop: index ? 18 : 0,
                    borderTop: index
                      ? "1px solid rgba(247, 240, 230, 0.16)"
                      : "none",
                  }}
                >
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                    <span className="chip chip-ink">{survey}</span>
                    {evidence?.module && (
                      <span className="chip chip-ink">{evidence.module}</span>
                    )}
                    {evidence?.uncertain && (
                      <span className="chip chip-ink">Annotation uncertain</span>
                    )}
                  </div>
                  {evidence ? (
                    <>
                      <SurveyQuestion evidence={evidence} as="p" dark />
                      {(evidence.timeline?.length ?? 0) > 0 && (
                        <div style={{ marginTop: 16 }}>
                          <TimelineChart
                            data={evidence.timeline}
                            height={140}
                            dark
                          />
                        </div>
                      )}
                      {(evidence.timeline?.length ?? 0) === 0 && (
                        <div style={{ marginTop: 16 }}>
                          <CoverageChart
                            waves={evidence.availableWaves}
                            countryCount={evidence.countryCount}
                            dark
                          />
                        </div>
                      )}
                      <p className="insight-board-evidence-text">
                        {evidence.insight}
                      </p>
                    </>
                  ) : (
                    <p className="insight-board-text">
                      No directly aligned {survey} question was retrieved. This
                      slot remains explicit instead of being filled with a
                      tangential source.
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
