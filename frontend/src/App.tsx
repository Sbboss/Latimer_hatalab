import { useEffect, useMemo, useRef, useState } from "react";
import { Cockpit } from "./components/Cockpit";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { Nav } from "./components/Nav";
import { SocialEvidence } from "./components/SocialEvidence";
import { Workspace } from "./components/Workspace";
import { mockAnalyzeModels, SAMPLE_TEXT } from "./data/mockAnalysis";
import { analyzeText, fetchModelNames, pingApi } from "./lib/api";
import type { ApiStatus, EvidenceQuestion, ModelAnalysis } from "./lib/types";

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
  const [modelNames, setModelNames] = useState<string[] | null>(null);

  const workspaceRef = useRef<HTMLDivElement>(null);
  const evidenceRef = useRef<HTMLDivElement>(null);
  const cockpitRef = useRef<HTMLDivElement>(null);

  const activeModel = analysisModels[activeModelIndex] ?? analysisModels[0];
  const activeAnalysis = activeModel?.result;

  const selectedHighlight = useMemo(
    () =>
      activeAnalysis?.highlights.find((h) => h.id === selectedId) ??
      activeAnalysis?.highlights[0] ??
      null,
    [activeAnalysis, selectedId]
  );

  const activeEvidence = useMemo(() => {
    const seen = new Set<string>();
    const evidence: EvidenceQuestion[] = [];

    selectedHighlight?.evidence?.forEach((item) => {
      if (!item?.question || seen.has(item.question)) return;
      seen.add(item.question);
      evidence.push(item);
    });

    return evidence.slice(0, 3);
  }, [selectedHighlight]);

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

  async function handleAnalyze() {
    setIsAnalyzing(true);
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

  function handleModelSelect(index: number) {
    setActiveModelIndex(index);
    setSelectedId(
      analysisModels[index]?.result.highlights[0]?.id ?? selectedId
    );
  }

  function handleHighlightSelect(id: string) {
    setSelectedId(id);

    const target = cockpitRef.current;
    if (!target) return;

    // Slow, controlled scroll that centers the cockpit card in viewport.
    const targetRect = target.getBoundingClientRect();
    const absoluteTargetTop = window.scrollY + targetRect.top;
    const desiredScrollY = absoluteTargetTop - (window.innerHeight - targetRect.height) / 2;
    const maxScrollY = document.documentElement.scrollHeight - window.innerHeight;
    const clampedTargetY = Math.max(0, Math.min(desiredScrollY, Math.max(0, maxScrollY)));

    const startY = window.scrollY;
    const distance = clampedTargetY - startY;
    const durationMs = 850;
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
            apiSource={apiSource}
          />

          <div
            ref={cockpitRef}
            className="container"
            style={{ paddingTop: 8, paddingBottom: 8 }}
          >
            <Cockpit
              highlight={selectedHighlight}
              models={analysisModels}
              activeModelIndex={activeModelIndex}
              onModelSelect={handleModelSelect}
            />
          </div>
        </div>

        <div ref={evidenceRef}>
          <SocialEvidence evidence={activeEvidence} />
        </div>

        <HowItWorks />
      </main>

      <Footer />
    </>
  );
}
