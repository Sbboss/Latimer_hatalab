import type { Highlight, ModelAnalysis } from "../lib/types";
import { groupEvidenceBySurvey, SURVEY_ORDER } from "../lib/evidence";
import { ResponseDataNotice } from "./ResponseDataNotice";
import { DimensionsBars } from "./DimensionsBars";
import { SurveyQuestion } from "./SurveyQuestion";
import { TimelineChart } from "./TimelineChart";
import { biasLevel } from "../lib/biasLevel";

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
            <div className="insight-board-eyebrow">Analysis complete</div>
            <h2 className="insight-board-phrase">No material bias signals found.</h2>
            <p className="insight-board-text insight-board-empty-copy">
              This analysis found no language pattern strong enough to highlight.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show every model that returned a result, beyond the ones that
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
  const evidenceItems = SURVEY_ORDER
    .map((survey) => ({ survey, evidence: evidenceBySurvey[survey][0] }))
    .filter(({ evidence }) => Boolean(evidence));
  const allEvidenceBySurvey = groupEvidenceBySurvey(
    highlight.evidence,
    Number.MAX_SAFE_INTEGER
  );
  const allEvidenceCount = SURVEY_ORDER.reduce(
    (count, survey) => count + allEvidenceBySurvey[survey].length,
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
          </div>
        </div>

        <div className="insight-board-strength">
          <div className="insight-board-strength-num">
            {highlight.score.toFixed(2)}
          </div>
          <div className="insight-board-strength-label">{biasLevel(highlight.score).label}</div>
        </div>
      </div>

      <div className="insight-board-body">
        <div className="insight-board-col">
          <div className="insight-board-block">
            <div className="insight-board-h">What we noticed</div>
            <p className="insight-board-text">
              {highlight.explanation ||
                "The selected signal has no explanation yet. Try another model or analyze the text again."}
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
                  “{highlight.replacement || "A replacement is unavailable."}”
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

          {evidenceCount > 0 && <div className="insight-board-block" id="insight-board-evidence">
            <div className="insight-board-h">
              Survey context
            </div>
            {evidenceItems.map(({ survey, evidence }, index) => {
              if (!evidence) return null;
              return (
                <article
                  key={evidence.recordId ?? `${survey}-${index}`}
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
                    {evidence.module && (
                      <span className="chip chip-ink">{evidence.module}</span>
                    )}
                    {evidence.uncertain && (
                      <span className="chip chip-ink">Annotation uncertain</span>
                    )}
                  </div>
                  <SurveyQuestion evidence={evidence} as="p" dark />
                  {(evidence.timeline?.length ?? 0) > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <TimelineChart
                        data={evidence.timeline}
                        height={140}
                        dark
                        responseLabel={evidence.timelineResponseLabel}
                      />
                    </div>
                  )}
                  {(evidence.timeline?.length ?? 0) === 0 && (
                    <div style={{ marginTop: 16 }}>
                      <ResponseDataNotice evidence={evidence} dark />
                    </div>
                  )}
                </article>
              );
            })}
          </div>}
        </div>
      </div>
      {evidenceCount > 0 && (
        <a className="insight-continuation" href="#social-evidence">
          <span>
            {allEvidenceCount > evidenceCount
              ? "Continue to more survey questions"
              : "View full survey evidence"}
          </span>
          <span aria-hidden>↓</span>
        </a>
      )}
    </div>
  );
}
