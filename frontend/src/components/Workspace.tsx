import { useEffect, useRef, useState } from "react";
import type { AnalysisResult, ModelAnalysis } from "../lib/types";
import { HighlightedText } from "./HighlightedText";
import { Check, Pencil, Reload, Sparkle } from "./Icons";

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
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisState: "idle" | "running" | "complete";
  apiSource: "live" | "mock" | "unknown";
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
  isAnalyzing,
  analysisProgress,
  analysisState,
  apiSource,
}: Props) {
  const taRef = useRef<HTMLTextAreaElement>(null);
  const [flippedModels, setFlippedModels] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (mode === "editing") {
      taRef.current?.focus();
    }
  }, [mode]);

  const activeModel = modelResults[activeModelIndex] ?? modelResults[0];

  const toggleFlip = (index: number) =>
    setFlippedModels((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));

  return (
    <section className="section" id="workspace">
      <div className="container">
        <div className="workspace-intro workspace-intro-compact">
          <div>
            <span className="section-eyebrow">01 · Live workspace</span>
            <h2 className="section-heading">
              Paste a sentence. Compare every model’s bias readout.
            </h2>
          </div>
        </div>

          <div
            className={`editor-card${
              analysisState === "complete" ? " is-analysis-complete" : ""
            }`}
          >
            <div className="editor-head">
              <div>
                <span className="editor-title">
                  {mode === "analyzed" ? "Analyzed document" : "Draft document"}
                </span>
                <div className="model-badge-row">
                  <span className="chip chip-accent">Active model: {activeModel.model}</span>
                </div>
              </div>

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
                      : "Comparing configured models"}
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
                    ref={taRef}
                    className="editor-textarea"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Paste a sentence or paragraph to analyze for hidden assumptions…"
                  />
                )}
              </div>

              <aside className="editor-scores">
                <div className="score-panel">
                  <div className="score-panel-head">
                    <span className="section-eyebrow">LLM scorebook</span>
                    <h3 className="score-panel-title">All model scores</h3>
                    <span className="score-panel-hint">Scroll sideways to compare</span>
                  </div>

                  <div className="score-panel-list">
                    {modelResults.map((model, index) => {
                      const flipped = flippedModels[index] === true;

                      return (
                        <button
                          key={model.model}
                          type="button"
                          className={`model-score-card ${index === activeModelIndex ? "is-active" : ""} ${flipped ? "is-flipped" : ""}`}
                          onClick={() => {
                            onModelSelect(index);
                            toggleFlip(index);
                          }}
                        >
                          <div className="model-card-face model-card-front">
                            <div className="model-score-meta">
                              <span>{model.model}</span>
                              <span>{model.overallScore.toFixed(2)}</span>
                            </div>
                            <div className="model-score-subtitle">
                              {model.result.highlights.length} trigger phrase{model.result.highlights.length === 1 ? "" : "s"}
                            </div>
                            <div className="category-chip-row">
                              {model.categories.slice(0, 3).map((category) => (
                                <span key={`${model.model}-${category.category}`} className="chip chip-quiet">
                                  {category.category} {Math.round(category.score * 100)}%
                                </span>
                              ))}
                            </div>
                          </div>

                          <div className="model-card-face model-card-back">
                            <div className="model-score-meta">
                              <span>Category breakdown</span>
                              <span>{model.overallScore.toFixed(2)}</span>
                            </div>
                            <div className="model-card-back-list">
                              {model.categories.map((category) => (
                                <div key={`${model.model}-back-${category.category}`} className="category-detail-row">
                                  <span>{category.category}</span>
                                  <span>{Math.round(category.score * 100)}%</span>
                                </div>
                              ))}
                            </div>
                            <div className="model-card-back-hint">Tap again to hide breakdown.</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </aside>
            </div>



            <div className="editor-foot">
              <span>
                {mode === "analyzed"
                  ? `${analysis.highlights.length} highlighted phrase${
                      analysis.highlights.length === 1 ? "" : "s"
                    } · click any to inspect`
                  : `${inputText.length} characters · ready to analyze`}
              </span>
              <span>
                {apiSource === "live"
                  ? "Connected · live signals"
                  : apiSource === "mock"
                  ? "Curated demo data"
                  : "Initializing"}
              </span>
            </div>
          </div>
      </div>
    </section>
  );
}
