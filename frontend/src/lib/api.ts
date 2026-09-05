import type { AnalysisResponse, ExtractedPage, ModelAnalysis, ModelCatalog } from "./types";
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
export async function fetchModelCatalog(signal?: AbortSignal): Promise<ModelCatalog> {
  try {
    const r = await fetch(`${API_BASE}/models`, { signal });
    if (!r.ok) throw new Error("Model catalog unavailable");
    const j = await r.json();
    const models = orderModelNames(
      Array.isArray(j?.models) && j.models.length ? j.models : DEFAULT_MODEL_NAMES
    );
    const defaultModels = orderModelNames(
      Array.isArray(j?.defaultModels) && j.defaultModels.length
        ? j.defaultModels
        : models.filter((name) => /^(gpt|claude)/i.test(name)).slice(0, 2)
    );
    return { models, defaultModels: defaultModels.length ? defaultModels : models.slice(0, 2) };
  } catch {
    const models = orderModelNames(DEFAULT_MODEL_NAMES);
    return { models, defaultModels: models.slice(0, 2) };
  }
}

export async function analyzeText(
  text: string,
  opts: { preferLive?: boolean; modelNames?: string[]; selectedModels?: string[] } = {}
): Promise<{ models: ModelAnalysis[]; source: "live" | "mock" }> {
  if (opts.preferLive !== false) {
    try {
      const r = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text, models: opts.selectedModels }),
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
    models: orderModelAnalyses(
      mockAnalyzeModels(text, opts.selectedModels ?? opts.modelNames)
    ),
    source: "mock",
  };
}

export async function extractPageText(url: string): Promise<ExtractedPage> {
  const r = await fetch(`${API_BASE}/extract-url`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url }),
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(body?.detail || "The page is unavailable for retrieval.");
  }
  return body as ExtractedPage;
}
