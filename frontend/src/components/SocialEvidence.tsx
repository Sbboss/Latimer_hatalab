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
              Five decades of public attitudes, behind every signal.
            </h2>
          </div>
          <p className="section-lede" style={{ marginTop: 0, maxWidth: 420 }}>
            Each detection is grounded in real survey questions about how
            Americans have answered, year after year. Bias signals carry the
            weight of evidence, not opinion.
          </p>
        </div>

        <div className="evidence-grid">
          {(evidence && evidence.length > 0 ? evidence : featuredEvidence).map((ev, index) => {
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
                    <span className="chip chip-accent">Question {index + 1}</span>
                    <span className="chip chip-accent">{ev.category}</span>
                  </div>
                  <span className="evidence-meta-date">
                    {hasTimeline ? `${first.year}–${last.year}` : "Trend unknown"}
                  </span>
                </div>

                <h3 className="evidence-q">“{extractQuestionText(ev.question)}”</h3>

                <div className="evidence-chart">
                  {hasTimeline ? (
                    <TimelineChart data={timeline} height={130} showAxis={false} />
                  ) : (
                    <div className="evidence-chart-empty">Trend data unavailable</div>
                  )}
                </div>

                <p className="evidence-insight">{ev.insight}</p>

                <div className="evidence-foot">
                  <span>Public support</span>
                  <span>{deltaDisplay} pts</span>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
