import { ArrowRight } from "./Icons";

type Props = {
  onAnalyze: () => void;
};

export function Hero({ onAnalyze }: Props) {
  return (
    <section className="hero" id="top">
      <div className="container hero-grid">
        <div>
          <h1>
            See the assumptions. <em>Change the thinking.</em>
          </h1>

          <p className="hero-sub">
            Understand the social assumptions behind language before you rewrite it.
          </p>

          <div className="hero-cta">
            <button className="btn btn-accent" onClick={onAnalyze}>
              Start analysis <ArrowRight size={16} />
            </button>
          </div>

        </div>

        <div className="preview">
          <div className="preview-head">
            <span className="preview-label">A signal worth examining</span>
            <span className="preview-score">High · 0.78</span>
          </div>

          <p className="preview-quote">
            “The candidate seemed <span className="hl">surprisingly articulate</span>.”
          </p>

          <div className="preview-insight">
            <span>Why it matters</span>
            <p>“Surprisingly” reveals an expectation gap: articulate speech was unexpected for this person.</p>
          </div>
          <div className="preview-reflection">
            <span>Reflect</span>
            <p>What made clear communication feel surprising here?</p>
          </div>
        </div>
      </div>
    </section>
  );
}
