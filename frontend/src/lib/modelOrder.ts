import type { ModelAnalysis } from "./types";

const MODEL_PREFIX_ORDER = ["gpt-5.5", "claude-opus", "deepseek", "llama"];

function modelPriority(name: string): number {
  const normalized = name.trim().toLowerCase();
  const priority = MODEL_PREFIX_ORDER.findIndex((prefix) =>
    normalized.startsWith(prefix)
  );
  return priority === -1 ? MODEL_PREFIX_ORDER.length : priority;
}

export function orderModelNames(names: string[]): string[] {
  return names
    .map((name, index) => ({ name, index }))
    .sort(
      (a, b) =>
        modelPriority(a.name) - modelPriority(b.name) || a.index - b.index
    )
    .map(({ name }) => name);
}

export function orderModelAnalyses(models: ModelAnalysis[]): ModelAnalysis[] {
  return models
    .map((model, index) => ({ model, index }))
    .sort(
      (a, b) =>
        modelPriority(a.model.model) - modelPriority(b.model.model) ||
        a.index - b.index
    )
    .map(({ model }) => model);
}
