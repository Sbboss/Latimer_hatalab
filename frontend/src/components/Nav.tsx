type Props = {
  view: "home" | "about";
  hasEvidence: boolean;
  onOpenAbout: () => void;
  onOpenHome: (target?: string) => void;
};

export function Nav({ view, hasEvidence, onOpenAbout, onOpenHome }: Props) {
  return (
    <header className="nav">
      <div className="container nav-row">
        <a className="brand" href="#top" onClick={() => onOpenHome("top")}>
          <span className="brand-mark" aria-hidden />
          <span>Bias Intelligence</span>
        </a>

        <nav className="nav-links" aria-label="Primary">
          {view === "home" ? (
            <>
              <a href="#workspace">Analyze</a>
              {hasEvidence && <a href="#social-evidence">Evidence</a>}
            </>
          ) : (
            <a href="#top" onClick={() => onOpenHome("top")}>Home</a>
          )}
          <a
            href="#about"
            aria-current={view === "about" ? "page" : undefined}
            onClick={onOpenAbout}
          >
            About
          </a>
        </nav>
      </div>
    </header>
  );
}
