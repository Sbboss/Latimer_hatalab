import { ArrowRight } from "./Icons";
import { TimelineChart } from "./TimelineChart";

type Props = {
  onAnalyze: () => void;
  onExploreEvidence: () => void;
};

const previewTimeline = [
  { year: 1972, support: 74 },
  { year: 1985, support: 82 },
  { year: 1996, support: 90 },
  { year: 2008, support: 94 },
  { year: 2022, support: 97 },
];

export function Hero({ onAnalyze, onExploreEvidence }: Props) {
  return (
    <section className="hero" id="top">
      <div className="container hero-grid">
        <div>
          <span className="hero-eyebrow">
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "var(--accent)",
              }}
            />
            Research prototype
          </span>

          <h1>
            From hidden assumptions to <em>measurable bias signals.</em>
          </h1>

          <p className="hero-sub">
            Reveal hidden assumptions in text with social evidence and
            explainable bias signals.
          </p>

          <div className="hero-cta">
            <button className="btn btn-accent" onClick={onAnalyze}>
              Analyze sample text <ArrowRight size={16} />
            </button>
            <button className="btn btn-ghost" onClick={onExploreEvidence}>
              Explore the evidence
            </button>
          </div>

          <div className="hero-meta">
            <div>
              <strong>8 dimensions</strong>
              <div>Race · Gender · Class · Sexuality · …</div>
            </div>
            <div>
              <strong>50+ years</strong>
              <div>of public-attitude grounding</div>
            </div>
            <div>
              <strong>Structured signals</strong>
              <div>Highlights · scores · rewrites</div>
            </div>
          </div>
        </div>

        <div className="preview" aria-hidden>
          <div className="preview-head">
            <div className="preview-dots">
              <span />
              <span />
              <span />
            </div>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "var(--ink-3)",
              }}
            >
              Bias signal · 0.78
            </span>
          </div>

          <p className="preview-quote">
            “The candidate seemed{" "}
            <span className="hl">surprisingly articulate</span> for the role,
            and may not be quite{" "}
            <span className="hl">leadership material</span> yet.”
          </p>

          <div className="preview-panel">
            <div>
              <div className="preview-score-num">0.78</div>
              <div className="preview-score-label">Signal · High</div>
            </div>
            <div>
              <div className="preview-insight">
                Coded assumptions about communication and leadership readiness.
              </div>
            </div>
          </div>

          <div style={{ marginTop: 22 }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "var(--ink-3)",
                marginBottom: 8,
              }}
            >
              Public attitude · Women in leadership
            </div>
            <TimelineChart data={previewTimeline} height={92} />
          </div>
        </div>
      </div>
    </section>
  );
}
