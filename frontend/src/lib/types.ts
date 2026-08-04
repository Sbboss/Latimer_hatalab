// Frontend ↔ backend contract.
// See backend/README.md for the canonical spec.

export type TimelinePoint = {
  year: number;
  support: number; // 0..100
};

export type EvidenceQuestion = {
  question: string;
  category: string; // human-facing label only
  insight: string;
  timeline: TimelinePoint[];
};

export type Dimension = {
  label: string;
  score: number; // 0..1
};

export type Highlight = {
  id: string;
  phrase: string;
  start: number;
  end: number;
  category: string;
  score: number;
  explanation: string;
  replacement: string;
  rewriteReason: string;
  dimensions: Dimension[];
  evidence: EvidenceQuestion[];
};

export type AnalysisResult = {
  inputText: string;
  overallScore: number;
  confidence: number;
  signalLabel: string;
  highlights: Highlight[];
  // The model's internal reasoning/scratchpad trace (Claude extended
  // thinking, or an OpenAI reasoning-model summary), when the provider
  // exposes one. Absent/undefined for models that don't support it.
  thinking?: string | null;
};

export type CategoryScore = {
  category: string;
  score: number; // 0..1
};

export type ModelAnalysis = {
  model: string;
  result: AnalysisResult;
  overallScore: number;
  confidence: number;
  categories: CategoryScore[];
  thinking?: string | null;
};

export type AnalysisResponse = {
  models: ModelAnalysis[];
};

export type ApiStatus = "live" | "mock" | "unknown";
