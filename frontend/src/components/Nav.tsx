import type { ApiStatus } from "../lib/types";
import { ArrowRight } from "./Icons";

type Props = {
  apiStatus: ApiStatus;
  onOpenWorkspace: () => void;
};

export function Nav({ apiStatus, onOpenWorkspace }: Props) {
  const statusText =
    apiStatus === "live"
      ? "Connected · live signals"
      : apiStatus === "mock"
      ? "Curated dataset · offline"
      : "Initializing";

  return (
    <header className="nav">
      <div className="container nav-row">
        <a className="brand" href="#top">
          <span className="brand-mark" aria-hidden />
          <span>Bias Intelligence</span>
        </a>

        <nav className="nav-links" aria-label="Primary">
          <a href="#workspace">Workspace</a>
          <a href="#insight-board">Insight Board</a>
          <a href="#social-evidence">Evidence</a>
          <a href="#method">Method</a>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <span className={`nav-status ${apiStatus === "live" ? "live" : ""}`}>
            <span className="pulse" aria-hidden />
            {statusText}
          </span>
          <button className="btn btn-quiet" onClick={onOpenWorkspace}>
            Open workspace <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}
