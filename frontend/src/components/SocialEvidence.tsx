import type { EvidenceQuestion } from "../lib/types";
import { featuredEvidence } from "../data/mockAnalysis";
import { groupEvidenceBySurvey, SURVEY_ORDER } from "../lib/evidence";
import { ResponseDataNotice } from "./ResponseDataNotice";
import { SurveyQuestion } from "./SurveyQuestion";
import { TimelineChart } from "./TimelineChart";

type Props = {
  evidence?: EvidenceQuestion[];
};

export function SocialEvidence({ evidence }: Props) {
  const evidenceItems = evidence ?? featuredEvidence;
  if (evidenceItems.length === 0) return null;

  const evidenceBySurvey = groupEvidenceBySurvey(evidenceItems, 2);
  const balancedEvidence = [0, 1].flatMap((rank) =>
    SURVEY_ORDER.map((survey) => ({
      survey,
      evidence: evidenceBySurvey[survey][rank],
      rank,
    }))
  ).filter(({ evidence: item }) => Boolean(item));

  if (balancedEvidence.length === 0) return null;

  return (
    <section
      className="section"
      id="social-evidence"
      aria-labelledby="social-evidence-title"
    >
      <div className="container">
        <header className="section-intro">
          <div>
            <h2 className="section-heading" id="social-evidence-title">
              More questions behind this signal.
            </h2>
          </div>
        </header>

        <div className="evidence-grid" aria-label="GSS and ISSP survey questions">
          {balancedEvidence.map(({ survey, evidence: ev, rank }) => {
            if (!ev) return null;

            const timeline = ev.timeline ?? [];
            const hasTimeline = timeline.length > 0;
            const first = timeline[0]!;
            const last = timeline[timeline.length - 1]!;
            return (
              <article
                className="evidence-card card"
                key={ev.recordId ?? `${survey}-${rank}-${ev.question}`}
              >
                <div className="evidence-meta">
                  <div className="evidence-meta-tags">
                    <span className="chip chip-accent">{survey}</span>
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

                <SurveyQuestion evidence={ev} />

                <div className="evidence-chart">
                  {hasTimeline ? (
                    <TimelineChart
                      data={timeline}
                      height={130}
                      showAxis={false}
                      responseLabel={ev.timelineResponseLabel}
                    />
                  ) : (
                    <ResponseDataNotice evidence={ev} />
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
