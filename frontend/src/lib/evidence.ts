import type { EvidenceQuestion } from "./types";

export const SURVEY_ORDER = ["GSS", "ISSP"] as const;

export type SurveyName = (typeof SURVEY_ORDER)[number];

export function evidenceSurvey(evidence: EvidenceQuestion): SurveyName | null {
  const explicitSurvey = evidence.survey?.trim().toUpperCase();
  if (explicitSurvey === "GSS" || explicitSurvey === "ISSP") {
    return explicitSurvey;
  }
  if (evidence.recordId?.startsWith("ISSP_")) {
    return "ISSP";
  }
  if (evidence.recordId) {
    return "GSS";
  }
  return null;
}

export function groupEvidenceBySurvey(
  evidence: EvidenceQuestion[] | undefined,
  perSurveyLimit: number
): Record<SurveyName, EvidenceQuestion[]> {
  const groups: Record<SurveyName, EvidenceQuestion[]> = {
    GSS: [],
    ISSP: [],
  };
  if (!evidence || perSurveyLimit <= 0) {
    return groups;
  }

  const seen = new Set<string>();
  evidence.forEach((item) => {
    const survey = evidenceSurvey(item);
    if (!survey || groups[survey].length >= perSurveyLimit) return;

    const identity = item.recordId ?? `${survey}:${item.question}`;
    if (!item.question || seen.has(identity)) return;
    seen.add(identity);
    groups[survey].push(item);
  });

  return groups;
}

export function selectBalancedEvidence(
  evidence: EvidenceQuestion[] | undefined,
  perSurveyLimit: number
): EvidenceQuestion[] {
  const groups = groupEvidenceBySurvey(evidence, perSurveyLimit);
  const selected: EvidenceQuestion[] = [];

  for (let rank = 0; rank < perSurveyLimit; rank += 1) {
    SURVEY_ORDER.forEach((survey) => {
      const item = groups[survey][rank];
      if (item) selected.push(item);
    });
  }

  return selected;
}
