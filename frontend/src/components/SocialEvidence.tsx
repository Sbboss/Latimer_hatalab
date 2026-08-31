import type { EvidenceQuestion } from "../lib/types";
import { featuredEvidence } from "../data/mockAnalysis";
import { groupEvidenceBySurvey, SURVEY_ORDER } from "../lib/evidence";
import { CoverageChart } from "./CoverageChart";
import { SurveyQuestion } from "./SurveyQuestion";
import { TimelineChart } from "./TimelineChart";

type Props = {
  evidence?: EvidenceQuestion[];
};

export function SocialEvidence({ evidence }: Props) {
  const evidenceItems = evidence ?? featuredEvidence;
  const evidenceBySurvey = groupEvidenceBySurvey(evidenceItems, 2);
  const evidenceSlots = [0, 1].flatMap((rank) =>
    SURVEY_ORDER.map((survey) => ({
      survey,
      evidence: evidenceBySurvey[survey][rank],
      rank,
    }))
  );

  return (
    <section
      className="section"
      id="social-evidence"
      aria-labelledby="social-evidence-title"
    >
      <div className="container">
        <header className="section-intro">
          <div>
            <span className="section-eyebrow">03 · Social evidence</span>
            <h2 className="section-heading" id="social-evidence-title">
              Survey questions behind each signal.
            </h2>
          </div>
          <p className="section-lede section-lede-compact">
            Question coverage is not an opinion trend.
          </p>
        </header>

        <div className="evidence-grid" aria-label="Two GSS and two ISSP questions">
          {evidenceSlots.map(({ survey, evidence: ev, rank }) => {
            if (!ev) {
              return (
                <article
                  className="evidence-card card evidence-card-missing"
                  key={`${survey}-${rank}-missing`}
                >
                  <div className="evidence-meta-tags">
                    <span className="chip chip-accent">{survey}</span>
                    <span className="chip chip-accent">
                      Evidence boundary
                    </span>
                  </div>
                  <h3 className="evidence-q">
                    No directly aligned {survey} question was retrieved.
                  </h3>
                  <p className="evidence-insight">
                    This reserved source slot stays explicit instead of being
                    filled with a tangential question from another survey.
                  </p>
                </article>
              );
            }

            const timeline = ev.timeline ?? [];
            const hasTimeline = timeline.length > 0;
            const first = timeline[0]!;
            const last = timeline[timeline.length - 1]!;
            const delta = hasTimeline ? last.support - first.support : 0;
            const deltaDisplay = `${delta > 0 ? "+" : ""}${delta.toFixed(2)}`;
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
                    <TimelineChart data={timeline} height={130} showAxis={false} />
                  ) : (
                    <CoverageChart
                      waves={ev.availableWaves}
                      countryCount={ev.countryCount}
                    />
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
