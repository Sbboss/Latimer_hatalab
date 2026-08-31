import { useEffect, useMemo, useRef, useState } from "react";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { InsightBoard } from "./components/InsightBoard";
import { Nav } from "./components/Nav";
import { SocialEvidence } from "./components/SocialEvidence";
import { Workspace } from "./components/Workspace";
import { mockAnalyzeModels, SAMPLE_TEXT } from "./data/mockAnalysis";
import { analyzeText, fetchModelNames, pingApi } from "./lib/api";
import { selectBalancedEvidence } from "./lib/evidence";
import type { ApiStatus, ModelAnalysis } from "./lib/types";

export default function App() {
  const initialModels = mockAnalyzeModels(SAMPLE_TEXT);
  const [analysisModels, setAnalysisModels] = useState<ModelAnalysis[]>(
    initialModels
  );
  const [inputText, setInputText] = useState<string>(SAMPLE_TEXT);
  const [mode, setMode] = useState<"analyzed" | "editing">("analyzed");
  const [activeModelIndex, setActiveModelIndex] = useState<number>(0);
  const [selectedId, setSelectedId] = useState<string | null>(
    initialModels[0]?.result.highlights[0]?.id ?? null
  );
  const [apiStatus, setApiStatus] = useState<ApiStatus>("unknown");
  const [apiSource, setApiSource] = useState<ApiStatus>("unknown");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisState, setAnalysisState] = useState<
    "idle" | "running" | "complete"
  >("idle");
  const [modelNames, setModelNames] = useState<string[] | null>(null);
  const completionAudioRef = useRef<AudioContext | null>(null);
  const completionResetRef = useRef<number | null>(null);

  const workspaceRef = useRef<HTMLDivElement>(null);
  const evidenceRef = useRef<HTMLDivElement>(null);
  const insightBoardRef = useRef<HTMLElement>(null);

  const activeModel = analysisModels[activeModelIndex] ?? analysisModels[0];
  const activeAnalysis = activeModel?.result;

  const selectedHighlight = useMemo(
    () =>
      activeAnalysis?.highlights.find((h) => h.id === selectedId) ??
      activeAnalysis?.highlights[0] ??
      null,
    [activeAnalysis, selectedId]
  );

  const activeEvidence = useMemo(
    () => selectBalancedEvidence(selectedHighlight?.evidence, 2),
    [selectedHighlight]
  );

  useEffect(() => {
    let cancelled = false;
    const ctrl = new AbortController();

    (async () => {
      const [ok, names] = await Promise.all([
        pingApi(ctrl.signal),
        fetchModelNames(ctrl.signal),
      ]);
      if (cancelled) return;
      setModelNames(names);
      setApiStatus(ok ? "live" : "mock");

      if (ok) {
        const { models, source } = await analyzeText(SAMPLE_TEXT, {
          preferLive: true,
          modelNames: names,
        });
        if (cancelled) return;
        if (models.length) {
          setAnalysisModels(models);
          setActiveModelIndex(0);
          setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
        }
        setApiSource(source);
      } else {
        // API is unreachable: replace the hardcoded placeholder models with
        // mock analysis using the *actually configured* model names.
        const models = mockAnalyzeModels(SAMPLE_TEXT, names);
        setAnalysisModels(models);
        setActiveModelIndex(0);
        setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
        setApiSource("mock");
      }
    })();

    return () => {
      cancelled = true;
      ctrl.abort();
    };
  }, []);

  useEffect(() => {
    if (
      activeAnalysis?.highlights.length &&
      selectedId &&
      !activeAnalysis.highlights.some((h) => h.id === selectedId)
    ) {
      setSelectedId(activeAnalysis.highlights[0]?.id ?? null);
    }
  }, [activeAnalysis, selectedId]);

  useEffect(() => {
    if (!isAnalyzing) return;
    const progressTimer = window.setInterval(() => {
      setAnalysisProgress((current) => {
        const increment = current < 35 ? 5 : current < 70 ? 2.5 : 1;
        return Math.min(92, current + increment);
      });
    }, 700);
    return () => window.clearInterval(progressTimer);
  }, [isAnalyzing]);

  useEffect(
    () => () => {
      if (completionResetRef.current !== null) {
        window.clearTimeout(completionResetRef.current);
      }
      void completionAudioRef.current?.close();
    },
    []
  );

  function prepareCompletionAudio() {
    if (completionAudioRef.current) return;
    const AudioContextClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!AudioContextClass) return;
    completionAudioRef.current = new AudioContextClass();
    void completionAudioRef.current.resume();
  }

  function playCompletionChime() {
    const context = completionAudioRef.current;
    if (!context) return;
    void context.resume();
    const start = context.currentTime + 0.02;
    const gain = context.createGain();
    gain.connect(context.destination);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.12, start + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.42);

    [659.25, 783.99].forEach((frequency, index) => {
      const oscillator = context.createOscillator();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      oscillator.connect(gain);
      oscillator.start(start + index * 0.11);
      oscillator.stop(start + 0.36 + index * 0.06);
    });
  }

  async function handleAnalyze() {
    if (isAnalyzing) return;
    prepareCompletionAudio();
    if (completionResetRef.current !== null) {
      window.clearTimeout(completionResetRef.current);
    }
    setIsAnalyzing(true);
    setAnalysisProgress(5);
    setAnalysisState("running");
    try {
      const { models, source } = await analyzeText(inputText, {
        preferLive: apiStatus === "live",
        modelNames: modelNames ?? undefined,
      });
      if (models.length) {
        setAnalysisModels(models);
        setActiveModelIndex(0);
        setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
      }
      setApiSource(source);
      setMode("analyzed");
      setAnalysisProgress(100);
      setAnalysisState("complete");
      playCompletionChime();
      completionResetRef.current = window.setTimeout(() => {
        setAnalysisState("idle");
        setAnalysisProgress(0);
      }, 5000);
    } finally {
      setIsAnalyzing(false);
    }
  }

  function scrollToWorkspace() {
    workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToEvidence() {
    const target = evidenceRef.current;
    if (!target) return;

    const targetRect = target.getBoundingClientRect();
    const absoluteTargetTop = window.scrollY + targetRect.top;
    const desiredScrollY = absoluteTargetTop - 88;
    const maxScrollY = document.documentElement.scrollHeight - window.innerHeight;
    const clampedTargetY = Math.max(0, Math.min(desiredScrollY, Math.max(0, maxScrollY)));

    const startY = window.scrollY;
    const distance = clampedTargetY - startY;
    const durationMs = 1200;
    const startTime = performance.now();

    const easeInOutCubic = (t: number) =>
      t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / durationMs);
      const eased = easeInOutCubic(progress);
      window.scrollTo(0, startY + distance * eased);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };

    requestAnimationFrame(step);
  }

  function scrollToInsightBoard() {
    const target = insightBoardRef.current;
    if (!target) return;

    const targetTop = window.scrollY + target.getBoundingClientRect().top - 88;
    window.scrollTo({ top: Math.max(0, targetTop), behavior: "smooth" });
  }

  function handleModelSelect(index: number) {
    setActiveModelIndex(index);
    setSelectedId(
      analysisModels[index]?.result.highlights[0]?.id ?? selectedId
    );
  }

  function handleHighlightSelect(id: string) {
    setSelectedId(id);
    requestAnimationFrame(scrollToInsightBoard);
  }

  return (
    <>
      <Nav apiStatus={apiStatus} onTryDemo={scrollToWorkspace} />

      <main>
        <Hero onAnalyze={scrollToWorkspace} onExploreEvidence={scrollToEvidence} />

        <div ref={workspaceRef}>
          <Workspace
            analysis={activeAnalysis!}
            modelResults={analysisModels}
            activeModelIndex={activeModelIndex}
            onModelSelect={handleModelSelect}
            inputText={inputText}
            setInputText={setInputText}
            mode={mode}
            setMode={setMode}
            selectedId={selectedId}
            onSelect={handleHighlightSelect}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            analysisProgress={analysisProgress}
            analysisState={analysisState}
            apiSource={apiSource}
          />

        </div>

        <section
          className="section insight-board-section"
          id="insight-board"
          ref={insightBoardRef}
          aria-labelledby="insight-board-title"
        >
          <div className="container">
            <header className="section-intro">
              <div>
                <span className="section-eyebrow">02 · Insight Board</span>
                <h2 className="section-heading" id="insight-board-title">
                  Understand the signal before changing the words.
                </h2>
              </div>
            </header>

            <InsightBoard
              highlight={selectedHighlight}
              models={analysisModels}
              activeModelIndex={activeModelIndex}
              onModelSelect={handleModelSelect}
            />
          </div>
        </section>

        <div ref={evidenceRef}>
          <SocialEvidence evidence={activeEvidence} />
        </div>

        <HowItWorks />
      </main>

      <Footer />
    </>
  );
}
