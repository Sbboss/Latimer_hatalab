import type { EvidenceQuestion } from "../lib/types";
import { featuredEvidence } from "../data/mockAnalysis";
import { TimelineChart } from "./TimelineChart";

type Props = {
  evidence?: EvidenceQuestion[];
};

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

export function SocialEvidence({ evidence }: Props) {
  const evidenceItems = evidence ?? featuredEvidence;

  return (
    <section className="section" id="evidence">
      <div className="container">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 24,
          }}
        >
          <div>
            <span className="section-eyebrow">02 · Social evidence</span>
            <h2 className="section-heading">
              Survey questions behind each signal.
            </h2>
          </div>
          <p className="section-lede" style={{ marginTop: 0, maxWidth: 420 }}>
            Retrieved GSS and ISSP questions show what researchers measured,
            where, and when. A trend appears only when actual response
            percentages are available.
          </p>
        </div>

        <div className="evidence-grid">
          {evidenceItems.length === 0 && (
            <article className="evidence-card card">
              <span className="chip chip-accent">Evidence boundary</span>
              <h3 className="evidence-q">
                No directly aligned survey question was retrieved.
              </h3>
              <p className="evidence-insight">
                The app leaves this section empty rather than presenting a
                tangential question as support.
              </p>
            </article>
          )}
          {evidenceItems.map((ev, index) => {
            const timeline = ev.timeline ?? [];
            const hasTimeline = timeline.length > 0;
            const first = timeline[0]!;
            const last = timeline[timeline.length - 1]!;
            const delta = hasTimeline ? last.support - first.support : 0;
            const deltaDisplay = `${delta > 0 ? "+" : ""}${delta.toFixed(2)}`;
            return (
              <article className="evidence-card card" key={`${ev.question}-${index}`}>
                <div className="evidence-meta">
                  <div className="evidence-meta-tags">
                    <span className="chip chip-accent">
                      {ev.survey ?? `Question ${index + 1}`}
                    </span>
                    <span className="chip chip-accent">{ev.category}</span>
                  </div>
                  <span className="evidence-meta-date">
                    {hasTimeline
                      ? `${first.year}–${last.year}`
                      : ev.availableWaves?.length
                      ? `${ev.availableWaves[0]}–${ev.availableWaves[ev.availableWaves.length - 1]}`
                      : "Waves unavailable"}
                  </span>
                </div>

                <h3 className="evidence-q">“{extractQuestionText(ev.question)}”</h3>

                <div className="evidence-chart">
                  {hasTimeline ? (
                    <TimelineChart data={timeline} height={130} showAxis={false} />
                  ) : (
                    <div className="evidence-chart-empty">
                      Question coverage only · no response trend in this record
                    </div>
                  )}
                </div>

                <p className="evidence-insight">{ev.insight}</p>

                <div className="evidence-foot">
                  <span>{hasTimeline ? "Observed response change" : "Question coverage"}</span>
                  <span>
                    {hasTimeline
                      ? `${deltaDisplay} pts`
                      : `${ev.availableWaves?.length ?? 0} waves`}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
