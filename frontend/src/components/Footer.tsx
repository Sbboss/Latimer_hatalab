export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-row">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          <span>Bias Intelligence</span>
        </div>
        <div className="footer-meta">Research prototype · v0.1</div>
        <div style={{ fontSize: 13, color: "var(--ink-3)", maxWidth: 360 }}>
          Bias signals indicate language patterns documented in social science
          literature. They are not moral judgments of the writer.
        </div>
      </div>
    </footer>
  );
}
