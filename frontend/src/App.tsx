import { useEffect, useMemo, useRef, useState } from "react";
import { Footer } from "./components/Footer";
import { About } from "./components/About";
import { Hero } from "./components/Hero";
import { InsightBoard } from "./components/InsightBoard";
import { Nav } from "./components/Nav";
import { SocialEvidence } from "./components/SocialEvidence";
import { Workspace } from "./components/Workspace";
import { mockAnalyzeModels, SAMPLE_TEXT } from "./data/mockAnalysis";
import { analyzeText, extractPageText, fetchModelCatalog, pingApi } from "./lib/api";
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
  const [view, setView] = useState<"home" | "about">(
    () => (window.location.hash === "#about" ? "about" : "home")
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisState, setAnalysisState] = useState<
    "idle" | "running" | "complete"
  >("idle");
  const [modelNames, setModelNames] = useState<string[] | null>(null);
  const [defaultModelNames, setDefaultModelNames] = useState<string[] | null>(null);
  const [analysisStatusText, setAnalysisStatusText] = useState("Comparing primary models");
  const [linkError, setLinkError] = useState<string | null>(null);
  const [sourceLabel, setSourceLabel] = useState<string | null>(null);
  const completionAudioRef = useRef<AudioContext | null>(null);
  const completionResetRef = useRef<number | null>(null);

  const workspaceRef = useRef<HTMLDivElement>(null);
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
      const [ok, catalog] = await Promise.all([
        pingApi(ctrl.signal),
        fetchModelCatalog(ctrl.signal),
      ]);
      if (cancelled) return;
      setModelNames(catalog.models);
      setDefaultModelNames(catalog.defaultModels);
      setApiStatus(ok ? "live" : "mock");

      if (ok) {
        const { models } = await analyzeText(SAMPLE_TEXT, {
          preferLive: true,
          modelNames: catalog.models,
          selectedModels: catalog.defaultModels,
        });
        if (cancelled) return;
        if (models.length) {
          setAnalysisModels(models);
          setActiveModelIndex(0);
          setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
        }
      } else {
        // API is unreachable: replace the hardcoded placeholder models with
        // mock analysis using the *actually configured* model names.
        const models = mockAnalyzeModels(SAMPLE_TEXT, catalog.defaultModels);
        setAnalysisModels(models);
        setActiveModelIndex(0);
        setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
      }
    })();

    return () => {
      cancelled = true;
      ctrl.abort();
    };
  }, []);

  useEffect(() => {
    const handleHashChange = () => {
      setView(window.location.hash === "#about" ? "about" : "home");
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
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

  async function handleAnalyze(scope: "primary" | "all") {
    if (isAnalyzing) return;
    const runAllModels = scope === "all";
    prepareCompletionAudio();
    if (completionResetRef.current !== null) {
      window.clearTimeout(completionResetRef.current);
    }
    setIsAnalyzing(true);
    setAnalysisProgress(5);
    setAnalysisState("running");
    setLinkError(null);
    try {
      let textForAnalysis = inputText;
      const potentialUrl = inputText.trim();
      if (/^https?:\/\/\S+$/i.test(potentialUrl)) {
        setAnalysisStatusText("Retrieving page text");
        try {
          const page = await extractPageText(potentialUrl);
          textForAnalysis = page.text;
          setInputText(page.text);
          setSourceLabel(page.title || page.url);
          setAnalysisProgress(24);
        } catch (error) {
          setLinkError(error instanceof Error ? error.message : "The page is unavailable for retrieval.");
          setAnalysisState("idle");
          setAnalysisProgress(0);
          return;
        }
      } else {
        setSourceLabel(null);
      }
      setAnalysisStatusText(runAllModels ? "Comparing all available models" : "Comparing primary models");
      const { models } = await analyzeText(textForAnalysis, {
        preferLive: apiStatus === "live",
        modelNames: modelNames ?? undefined,
        selectedModels: runAllModels ? modelNames ?? undefined : defaultModelNames ?? undefined,
      });
      if (models.length) {
        setAnalysisModels(models);
        setActiveModelIndex(0);
        setSelectedId(models[0]?.result.highlights[0]?.id ?? null);
      }
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

  function openAbout() {
    window.location.hash = "about";
    setView("about");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openHome(target = "top") {
    window.location.hash = target;
    setView("home");
    requestAnimationFrame(() => {
      document.getElementById(target)?.scrollIntoView({ behavior: "smooth" });
    });
  }

  return (
    <>
      <Nav
        view={view}
        hasEvidence={activeEvidence.length > 0}
        onOpenAbout={openAbout}
        onOpenHome={openHome}
      />

      {view === "about" ? (
        <main>
          <About onStart={() => openHome("workspace")} />
        </main>
      ) : (
      <main>
        <Hero onAnalyze={scrollToWorkspace} />

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
            onAnalyze={() => handleAnalyze("primary")}
            onAnalyzeMore={() => handleAnalyze("all")}
            canAnalyzeMore={(modelNames?.length ?? 0) > analysisModels.length}
            availableModelCount={modelNames?.length ?? analysisModels.length}
            isAnalyzing={isAnalyzing}
            analysisProgress={analysisProgress}
            analysisState={analysisState}
            analysisStatusText={analysisStatusText}
            linkError={linkError}
            sourceLabel={sourceLabel}
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
                <h2 className="section-heading" id="insight-board-title">
                  Understand before you rewrite.
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

        <SocialEvidence evidence={activeEvidence} />
      </main>
      )}

      <Footer />
    </>
  );
}
