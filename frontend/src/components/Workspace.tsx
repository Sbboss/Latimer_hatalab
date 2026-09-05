import { useEffect, useRef } from "react";
import type { AnalysisResult, ModelAnalysis } from "../lib/types";
import { HighlightedText } from "./HighlightedText";
import { Check, Pencil, Reload, Sparkle } from "./Icons";
import { biasLevel } from "../lib/biasLevel";

type Props = {
  analysis: AnalysisResult;
  modelResults: ModelAnalysis[];
  activeModelIndex: number;
  onModelSelect: (index: number) => void;
  inputText: string;
  setInputText: (s: string) => void;
  mode: "analyzed" | "editing";
  setMode: (m: "analyzed" | "editing") => void;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onAnalyze: () => void;
  onAnalyzeMore: () => void;
  canAnalyzeMore: boolean;
  availableModelCount: number;
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisState: "idle" | "running" | "complete";
  analysisStatusText: string;
  linkError: string | null;
  sourceLabel: string | null;
};

export function Workspace({
  analysis,
  modelResults,
  activeModelIndex,
  onModelSelect,
  inputText,
  setInputText,
  mode,
  setMode,
  selectedId,
  onSelect,
  onAnalyze,
  onAnalyzeMore,
  canAnalyzeMore,
  availableModelCount,
  isAnalyzing,
  analysisProgress,
  analysisState,
  analysisStatusText,
  linkError,
  sourceLabel,
}: Props) {
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (mode === "editing") {
      taRef.current?.focus();
    }
  }, [mode]);

  return (
    <section className="section" id="workspace">
      <div className="container">
        <div className="workspace-intro workspace-intro-compact">
          <div>
            <h2 className="section-heading">Analyze writing</h2>
            <p className="section-caption">Paste text or a public URL.</p>
          </div>
        </div>

          <div
            className={`editor-card${
              analysisState === "complete" ? " is-analysis-complete" : ""
            }`}
          >
            <div className="editor-head">
              <label className="editor-input-label" htmlFor="analysis-input">
                Text or public URL
              </label>
              <div className="editor-actions">
                {mode === "analyzed" ? (
                  <button
                    className="btn btn-quiet"
                    onClick={() => setMode("editing")}
                  >
                    <Pencil size={13} /> Edit text
                  </button>
                ) : (
                  <button
                    className="btn btn-quiet"
                    onClick={() => setMode("analyzed")}
                  >
                    Cancel
                  </button>
                )}
                <button
                  className={`btn btn-accent${
                    analysisState === "complete" ? " is-complete" : ""
                  }`}
                  onClick={onAnalyze}
                  disabled={isAnalyzing}
                >
                  {analysisState === "running" ? (
                    <>
                      <Reload size={14} /> Analyzing…
                    </>
                  ) : analysisState === "complete" ? (
                    <>
                      <Check size={15} /> Analysis complete
                    </>
                  ) : (
                    <>
                      <Sparkle size={14} /> Analyze text
                    </>
                  )}
                </button>
              </div>
            </div>

            {analysisState !== "idle" && (
              <div
                className={`analysis-progress${
                  analysisState === "complete" ? " is-complete" : ""
                }`}
                role="status"
                aria-live="polite"
              >
                <div className="analysis-progress-copy">
                  <span>
                    {analysisState === "complete"
                      ? "Analysis complete"
                      : analysisStatusText}
                  </span>
                  <span>{Math.round(analysisProgress)}%</span>
                </div>
                <div
                  className="analysis-progress-track"
                  role="progressbar"
                  aria-label="Analysis progress"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(analysisProgress)}
                >
                  <div
                    className="analysis-progress-fill"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
              </div>
            )}

            {linkError && <p className="editor-link-error" role="alert">{linkError}</p>}
            {sourceLabel && (
              <p className="editor-source-label">Analyzing page text from {sourceLabel}</p>
            )}

            <div className="editor-body">
              <div className="editor-main">
                {mode === "analyzed" ? (
                  <HighlightedText
                    text={analysis.inputText}
                    highlights={analysis.highlights}
                    selectedId={selectedId}
                    onSelect={onSelect}
                  />
                ) : (
                  <textarea
                    id="analysis-input"
                    ref={taRef}
                    className="editor-textarea"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Paste text or a public URL"
                  />
                )}
              </div>

              <aside className="editor-scores">
                <div className="score-panel">
                  <div className="score-panel-head">
                    <div className="score-panel-heading-copy">
                      <div className="score-panel-title-row">
                        <h3 className="score-panel-title">Model perspectives</h3>
                        <span className="score-panel-count">
                          {modelResults.length} of {availableModelCount}
                        </span>
                      </div>
                    </div>
                    {canAnalyzeMore && (
                      <button
                        className="btn score-expand-button"
                        onClick={onAnalyzeMore}
                        disabled={isAnalyzing}
                      >
                        <Sparkle size={14} /> Compare more models
                      </button>
                    )}
                  </div>

                  <div className="score-panel-list">
                    {modelResults.map((model, index) => {
                      const level = biasLevel(model.overallScore);

                      return (
                        <button
                          key={model.model}
                          type="button"
                          className={`model-score-card ${index === activeModelIndex ? "is-active" : ""}`}
                          onClick={() => onModelSelect(index)}
                        >
                          <div className="model-card-face">
                            <div className="model-score-meta">
                              <span className="model-score-name">{model.model}</span>
                              <span className="model-score-value">
                                {model.overallScore.toFixed(2)}
                              </span>
                            </div>
                            <span className="model-score-level">{level.label}</span>
                            <div className="model-score-subtitle">
                              {model.result.highlights.length} trigger phrase{model.result.highlights.length === 1 ? "" : "s"}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </aside>
            </div>
          </div>
      </div>
    </section>
  );
}
