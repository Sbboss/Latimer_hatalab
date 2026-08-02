const steps = [
  {
    n: "01",
    title: "Detect hidden assumptions",
    text: "A linguistic pattern library and an LLM detector flag phrases that have been documented to carry encoded social expectations.",
  },
  {
    n: "02",
    title: "Compare against social context",
    text: "Each phrase is grounded against five decades of GSS public-attitude data so signals reflect how people have actually responded over time.",
  },
  {
    n: "03",
    title: "Explain the bias signals",
    text: "Every highlight ships with a category, dimensions, a confidence, and a clear human-readable explanation — never raw model output.",
  },
  {
    n: "04",
    title: "Suggest less biased language",
    text: "Each signal includes a softer rewrite that names the actual observation while removing the implied expectation gap.",
  },
];

export function HowItWorks() {
  return (
    <section className="section" id="method">
      <div className="container">
        <span className="section-eyebrow">03 · Method</span>
        <h2 className="section-heading">
          Built like a research instrument, used like a writing tool.
        </h2>
        <p className="section-lede">
          Bias Intelligence is not a grammar checker. It is a measurement
          surface — every signal is structured, explainable, and grounded in
          public-attitude data.
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
