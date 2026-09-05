export type BiasLevel = {
  label: "no bias" | "low bias" | "medium bias" | "high bias" | "very high bias";
  description: string;
};

export function biasLevel(score: number): BiasLevel {
  if (score < 0.2) return { label: "no bias", description: "No bias signal" };
  if (score < 0.4) return { label: "low bias", description: "Low bias signal" };
  if (score < 0.6) return { label: "medium bias", description: "Medium bias signal" };
  if (score < 0.8) return { label: "high bias", description: "High bias signal" };
  return { label: "very high bias", description: "Very high bias signal" };
}
