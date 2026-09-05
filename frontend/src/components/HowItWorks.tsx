const steps = [
  {
    n: "01",
    title: "Detect hidden assumptions",
    text: "A linguistic pattern library and an LLM detector flag phrases that have been documented to carry encoded social expectations.",
  },
  {
    n: "02",
    title: "Compare against social context",
    text: "Hybrid search matches each phrase to relevant GSS and ISSP questions, with survey, module, wave, and quality metadata kept visible.",
  },
  {
    n: "03",
    title: "Invite reflection",
    text: "Every highlight explains the signal and asks a non-accusatory question that helps you examine the assumption yourself.",
  },
  {
    n: "04",
    title: "Offer a concrete next step",
    text: "A specific rewrite is available after the explanation, so the tool supports action without replacing the learning process.",
  },
];

export function HowItWorks() {
  return (
    <section className="section" id="method">
      <div className="container">
        <span className="section-eyebrow">04 · Method</span>
        <h2 className="section-heading">
          Built like a research instrument, used like a writing tool.
        </h2>
        <p className="section-lede">
          Bias Intelligence goes beyond grammar checking. It is a learning surface:
          every signal is structured, explainable, and connected to attributable
          social-survey questions.
        </p>

        <div className="how-grid">
          {steps.map((s) => (
            <article className="how-card" key={s.n}>
              <div className="how-num">{s.n}</div>
              <div>
                <h3 className="how-title">{s.title}</h3>
                <p className="how-text" style={{ marginTop: 12 }}>
                  {s.text}
                </p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
