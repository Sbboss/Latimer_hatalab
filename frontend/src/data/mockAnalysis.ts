import type {
  AnalysisResult,
  CategoryScore,
  EvidenceQuestion,
  Highlight,
  ModelAnalysis,
} from "../lib/types";

// ---------------------------------------------------------------------------
// Demo input
// ---------------------------------------------------------------------------
export const SAMPLE_TEXT =
  "I think Sarah is surprisingly articulate for someone from a nontraditional background. " +
  "We need a strong cultural fit on this team, and while she's promising, she's not quite leadership material yet.";

// ---------------------------------------------------------------------------
// Phrase glossary used by the mock analyzer.
// Matches the curated glossary in backend/analysis.py so the demo behaves
// the same offline as it does against the live API.
// ---------------------------------------------------------------------------
type GlossaryEntry = Omit<Highlight, "id" | "start" | "end" | "phrase"> & {
  patterns: RegExp[];
};

const glossary: GlossaryEntry[] = [
  {
    patterns: [
      /surprisingly articulate/i,
      /remarkably articulate/i,
      /unexpectedly well[- ]spoken/i,
      /speaks english (?:so )?well/i,
    ],
    category: "Race & ethnicity",
    score: 0.81,
    explanation:
      "Modifiers like “surprisingly” imply that articulate speech was unexpected for this person. That expectation gap can encode assumptions about competence linked to race, ethnicity, or class.",
    replacement: "communicates clearly and persuasively",
    rewriteReason:
      "Removes the implied expectation gap and focuses on the observable communication quality.",
    dimensions: [
      { label: "Race & ethnicity", score: 0.81 },
      { label: "Economic background", score: 0.46 },
      { label: "Gender expectations", score: 0.18 },
    ],
    evidence: [
      {
        question:
          "Do you believe most differences in jobs, income, and housing between Black and White Americans are due to lack of motivation?",
        category: "Race & ethnicity",
        insight:
          "Public agreement with motivation-based explanations has fallen as awareness of structural factors has risen.",
        timeline: [
          { year: 1977, support: 64 },
          { year: 1990, support: 52 },
          { year: 2002, support: 44 },
          { year: 2014, support: 34 },
          { year: 2022, support: 28 },
        ],
      },
    ],
  },
  {
    patterns: [
      /nontraditional background/i,
      /non[- ]traditional background/i,
      /unconventional pedigree/i,
      /didn['’]t go to a (?:top|name[- ]brand) school/i,
    ],
    category: "Economic background",
    score: 0.67,
    explanation:
      "Framing a background as “nontraditional” centers an unstated default — usually a particular class, schooling, or career path. It can encode socioeconomic assumptions about who belongs.",
    replacement: "brings experience from a different professional path",
    rewriteReason:
      "Names the actual difference (path or experience) without implying that one path is the standard one.",
    dimensions: [
      { label: "Economic background", score: 0.74 },
      { label: "Race & ethnicity", score: 0.41 },
      { label: "Gender expectations", score: 0.22 },
    ],
    evidence: [
      {
        question:
          "Do you think people like you and your family have a good chance of improving their standard of living?",
        category: "Economic background",
        insight:
          "Belief in upward mobility has steadily declined, suggesting “traditional” pathways are no longer perceived as universal.",
        timeline: [
          { year: 1987, support: 75 },
          { year: 1996, support: 70 },
          { year: 2006, support: 64 },
          { year: 2014, support: 58 },
          { year: 2022, support: 52 },
        ],
      },
    ],
  },
  {
    patterns: [
      /(?:strong )?cultural fit/i,
      /(?:not a )?culture fit/i,
      /vibe (?:check|fit)/i,
    ],
    category: "Economic background",
    score: 0.71,
    explanation:
      "“Cultural fit” often substitutes for unstated similarity — to schooling, hobbies, or social class. Without explicit criteria it tends to reproduce the demographics already in the room.",
    replacement: "aligned with how this team collaborates and gives feedback",
    rewriteReason:
      "Replaces an opaque vibe judgment with concrete, observable collaboration behaviors that can be evaluated fairly.",
    dimensions: [
      { label: "Economic background", score: 0.71 },
      { label: "Race & ethnicity", score: 0.55 },
      { label: "Gender expectations", score: 0.34 },
    ],
    evidence: [
      {
        question:
          "How important is it that a coworker shares your social and cultural background?",
        category: "Economic background",
        insight:
          "Reported importance of shared background among coworkers has declined as workplaces have diversified.",
        timeline: [
          { year: 1985, support: 58 },
          { year: 1995, support: 50 },
          { year: 2005, support: 41 },
          { year: 2015, support: 33 },
          { year: 2022, support: 27 },
        ],
      },
    ],
  },
  {
    patterns: [
      /not quite leadership material/i,
      /not leadership material/i,
      /lacks executive presence/i,
      /too soft to lead/i,
    ],
    category: "Gender expectations",
    score: 0.78,
    explanation:
      "Phrases like “leadership material” often package a stereotype about how leaders look, sound, or carry themselves — assumptions that disproportionately filter out women and other groups.",
    replacement: "still developing the strategic experience this role calls for",
    rewriteReason:
      "Names the specific developmental gap rather than an inherent trait, which is both fairer and more actionable feedback.",
    dimensions: [
      { label: "Gender expectations", score: 0.78 },
      { label: "Race & ethnicity", score: 0.36 },
      { label: "Economic background", score: 0.29 },
    ],
    evidence: [
      {
        question:
          "If your party nominated a qualified woman for President, would you vote for her?",
        category: "Gender expectations",
        insight:
          "Public expectations around women’s leadership have shifted significantly over the past five decades.",
        timeline: [
          { year: 1972, support: 74 },
          { year: 1985, support: 82 },
          { year: 1996, support: 90 },
          { year: 2008, support: 94 },
          { year: 2022, support: 97 },
        ],
      },
    ],
  },
  {
    patterns: [/(?:she|he|they) is too emotional/i, /too emotional (?:for|to)/i, /hysterical/i],
    category: "Gender expectations",
    score: 0.69,
    explanation:
      "Calling a colleague “too emotional” is heavily gender-coded in research on workplace evaluations and tends to penalize the same behaviors that are praised as “passionate” elsewhere.",
    replacement: "expressed strong disagreement during the discussion",
    rewriteReason:
      "Describes the actual behavior without an emotion-coded judgment that the literature shows is applied unevenly by gender.",
    dimensions: [
      { label: "Gender expectations", score: 0.69 },
      { label: "Mental health", score: 0.31 },
      { label: "Economic background", score: 0.18 },
    ],
    evidence: [
      {
        question: "Do men make better political leaders than women do?",
        category: "Gender expectations",
        insight:
          "Agreement with this statement has fallen sharply, but a measurable minority still endorses it.",
        timeline: [
          { year: 1974, support: 47 },
          { year: 1990, support: 32 },
          { year: 2002, support: 24 },
          { year: 2014, support: 18 },
          { year: 2022, support: 14 },
        ],
      },
    ],
  },
  {
    patterns: [/openly gay/i, /flamboyant/i, /acts (?:gay|straight)/i],
    category: "Sexual orientation",
    score: 0.72,
    explanation:
      "Modifiers like “openly” mark non-heterosexuality as the noteworthy deviation from a default. The framing itself carries a normative expectation worth questioning.",
    replacement: "is gay",
    rewriteReason:
      "Drops the modifier that frames the identity as something requiring qualification.",
    dimensions: [
      { label: "Sexual orientation", score: 0.72 },
      { label: "Gender expectations", score: 0.34 },
      { label: "Religion & belief", score: 0.21 },
    ],
    evidence: [
      {
        question:
          "Do you think sexual relations between two adults of the same sex are always wrong?",
        category: "Sexual orientation",
        insight:
          "Disagreement with this statement has grown substantially as social attitudes have shifted.",
        timeline: [
          { year: 1973, support: 21 },
          { year: 1991, support: 24 },
          { year: 2004, support: 35 },
          { year: 2014, support: 56 },
          { year: 2022, support: 69 },
        ],
      },
    ],
  },
  {
    patterns: [/crazy/i, /unhinged/i, /psycho/i, /mentally unstable/i],
    category: "Mental health",
    score: 0.66,
    explanation:
      "Casual psychiatric language is one of the most common vectors of stigma. It often labels behavior we disagree with rather than describing what actually happened.",
    replacement: "behaved in a way I found difficult to follow",
    rewriteReason:
      "Describes the behavior without invoking mental-health language as shorthand for disagreement.",
    dimensions: [
      { label: "Mental health", score: 0.66 },
      { label: "Gender expectations", score: 0.24 },
      { label: "Political identity", score: 0.19 },
    ],
    evidence: [
      {
        question:
          "Would you be willing to work closely with someone who has received mental health treatment?",
        category: "Mental health",
        insight:
          "Reported willingness has risen significantly as awareness has grown, but stigma in workplace language persists.",
        timeline: [
          { year: 1996, support: 58 },
          { year: 2006, support: 66 },
          { year: 2014, support: 74 },
          { year: 2022, support: 81 },
        ],
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Mock analyzer (used when the API is unreachable).
// ---------------------------------------------------------------------------
export function mockAnalyze(text: string): AnalysisResult {
  const trimmed = (text || "").trim();
  const occupied: Array<[number, number]> = [];
  const found: Highlight[] = [];

  glossary.forEach((entry, entryIdx) => {
    entry.patterns.forEach((pattern) => {
      const re = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : pattern.flags + "g");
      let m: RegExpExecArray | null;
      while ((m = re.exec(trimmed)) !== null) {
        const start = m.index;
        const end = start + m[0].length;
        const overlaps = occupied.some(([s, e]) => !(end <= s || start >= e));
        if (overlaps) continue;
        occupied.push([start, end]);
        found.push({
          id: `h${found.length + 1}_${entryIdx}`,
          phrase: trimmed.slice(start, end),
          start,
          end,
          category: entry.category,
          score: entry.score,
          explanation: entry.explanation,
          replacement: entry.replacement,
          rewriteReason: entry.rewriteReason,
          dimensions: entry.dimensions,
          evidence: entry.evidence,
        });
      }
    });
  });

  found.sort((a, b) => a.start - b.start);
  found.forEach((h, i) => (h.id = `h${i + 1}`));

  const overall = found.length ? Math.max(...found.map((h) => h.score)) : 0;
  const signalLabel =
    overall >= 0.7
      ? "High signal"
      : overall >= 0.45
      ? "Moderate signal"
      : overall > 0
      ? "Low signal"
      : "No signal detected";

  return {
    inputText: trimmed,
    overallScore: Math.round(overall * 100) / 100,
    confidence: found.length ? 0.86 : 0,
    signalLabel,
    highlights: found,
  };
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function aggregateCategoryScores(highlights: Highlight[]): CategoryScore[] {
  const categoryMap: Record<string, number> = {};
  highlights.forEach((highlight) => {
    categoryMap[highlight.category] = Math.max(
      categoryMap[highlight.category] ?? 0,
      highlight.score
    );
  });
  return Object.entries(categoryMap)
    .map(([category, score]) => ({ category, score }))
    .sort((a, b) => b.score - a.score);
}

// Fallback used only if the backend's /api/models list can't be fetched at
// all (e.g. fully offline demo). Keep this in sync with the default
// AZURE_MODEL_DEPLOYMENTS_JSON in .env.example so it never shows a model
// that isn't actually configured.
export const DEFAULT_MODEL_NAMES = [
  "GPT-5.5",
  "Claude-Opus-4.6",
  "DeepSeek-V4-Pro",
  "Llama-3.3-70B-Instruct",
];

export function mockAnalyzeModels(
  text: string,
  modelNames: string[] = DEFAULT_MODEL_NAMES
): ModelAnalysis[] {
  const base = mockAnalyze(text);

  return modelNames.map((modelName, index) => {
    const offset = (index - 1) * 0.05;
    const result: AnalysisResult = {
      ...base,
      overallScore: clamp(base.overallScore + offset, 0, 1),
      confidence: clamp(base.confidence - offset * 0.5, 0, 1),
      highlights: base.highlights.map((highlight) => ({
        ...highlight,
        score: clamp(highlight.score + offset * 0.1, 0, 1),
      })),
    };

    return {
      model: modelName,
      result,
      overallScore: result.overallScore,
      confidence: result.confidence,
      categories: aggregateCategoryScores(result.highlights),
    };
  });
}

export const mockAnalysis: AnalysisResult = mockAnalyze(SAMPLE_TEXT);

// ---------------------------------------------------------------------------
// Standalone evidence cards used in the social-evidence section.
// These are independent of any specific highlight — they're a public-facing
// research showcase.
// ---------------------------------------------------------------------------
export const featuredEvidence: EvidenceQuestion[] = [
  {
    question:
      "If your party nominated a qualified woman for President, would you vote for her?",
    category: "Gender expectations",
    insight:
      "Public support has climbed from a slim majority in the 1970s to near-universal acceptance today.",
    timeline: [
      { year: 1972, support: 74 },
      { year: 1985, support: 82 },
      { year: 1996, support: 90 },
      { year: 2008, support: 94 },
      { year: 2022, support: 97 },
    ],
  },
  {
    question:
      "Do you think sexual relations between two adults of the same sex are always wrong?",
    category: "Sexual orientation",
    insight:
      "Disagreement has more than tripled in five decades, one of the fastest documented attitudinal shifts.",
    timeline: [
      { year: 1973, support: 21 },
      { year: 1991, support: 24 },
      { year: 2004, support: 35 },
      { year: 2014, support: 56 },
      { year: 2022, support: 69 },
    ],
  },
  {
    question:
      "Would you be willing to work closely with someone who has received mental health treatment?",
    category: "Mental health",
    insight:
      "Workplace willingness has risen meaningfully, even as stigmatizing language in everyday speech persists.",
    timeline: [
      { year: 1996, support: 58 },
      { year: 2006, support: 66 },
      { year: 2014, support: 74 },
      { year: 2022, support: 81 },
    ],
  },
];
