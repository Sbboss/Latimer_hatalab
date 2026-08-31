import type { AnalysisResponse, ModelAnalysis } from "./types";
import { DEFAULT_MODEL_NAMES, mockAnalyzeModels } from "../data/mockAnalysis";
import { orderModelAnalyses, orderModelNames } from "./modelOrder";

const API_BASE = "/api";

export async function pingApi(signal?: AbortSignal): Promise<boolean> {
  try {
    const r = await fetch(`${API_BASE}/health`, { signal });
    if (!r.ok) return false;
    const j = await r.json();
    return j?.status === "ok";
  } catch {
    return false;
  }
}

// Fetches the actual configured model deployments from the backend, so the
// UI (including mock/placeholder state) never shows a model name that isn't
// really wired up in .env. Falls back to DEFAULT_MODEL_NAMES if unreachable.
export async function fetchModelNames(signal?: AbortSignal): Promise<string[]> {
  try {
    const r = await fetch(`${API_BASE}/models`, { signal });
    if (!r.ok) return DEFAULT_MODEL_NAMES;
    const j = await r.json();
    return orderModelNames(
      Array.isArray(j?.models) && j.models.length ? j.models : DEFAULT_MODEL_NAMES
    );
  } catch {
    return orderModelNames(DEFAULT_MODEL_NAMES);
  }
}

export async function analyzeText(
  text: string,
  opts: { preferLive?: boolean; modelNames?: string[] } = {}
): Promise<{ models: ModelAnalysis[]; source: "live" | "mock" }> {
  if (opts.preferLive !== false) {
    try {
      const r = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (r.ok) {
        const j = (await r.json()) as AnalysisResponse;
        if (j?.models?.length) {
          return { models: orderModelAnalyses(j.models), source: "live" };
        }
      }
    } catch {
      // fall through to mock
    }
  }
  return {
    models: orderModelAnalyses(mockAnalyzeModels(text, opts.modelNames)),
    source: "mock",
  };
}
