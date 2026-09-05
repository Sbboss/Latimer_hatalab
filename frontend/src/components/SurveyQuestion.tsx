import type { EvidenceQuestion } from "../lib/types";
import { Doc } from "./Icons";

type Props = {
  evidence: EvidenceQuestion;
  as?: "h3" | "p";
  dark?: boolean;
};

function cleanQuestionText(content: string | undefined): string {
  const lines = (content ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) return "Question wording unavailable";
  const firstLine = lines[0];
  return firstLine.toLowerCase().startsWith("question:")
    ? firstLine.slice(9).trim()
    : firstLine;
}

export function coverageSummary(evidence: EvidenceQuestion): string {
  const waves = evidence.availableWaves?.length ?? 0;
  const waveText = waves
    ? `Asked in ${waves} survey wave${waves === 1 ? "" : "s"}`
    : "Survey waves unavailable";
  const countryText =
    typeof evidence.countryCount === "number"
      ? ` across ${evidence.countryCount} countr${
          evidence.countryCount === 1 ? "y" : "ies"
        }`
      : "";
  return `${waveText}${countryText}.`;
}

export function SurveyQuestion({ evidence, as = "h3", dark = false }: Props) {
  const QuestionTag = as;
  const plainQuestion = cleanQuestionText(evidence.question);
  const originalQuestion = cleanQuestionText(
    evidence.originalQuestion ?? evidence.question
  );
  const isIssp = evidence.survey?.toUpperCase() === "ISSP";
  const showOriginal = isIssp || originalQuestion !== plainQuestion;

  return (
    <>
      <QuestionTag
        className={as === "h3" ? "evidence-q" : "insight-board-question"}
      >
        “{plainQuestion}”
      </QuestionTag>
      <p className={dark ? "insight-board-provenance" : "evidence-summary"}>
        {coverageSummary(evidence)}
      </p>
      {showOriginal && (
        <details className={`source-disclosure${dark ? " is-dark" : ""}`}>
          <summary>
            <Doc size={14} /> View original survey wording
          </summary>
          <div className="source-disclosure-body">
            <p>“{originalQuestion}”</p>
            {evidence.sourceDataset && (
              <p>Source dataset: {evidence.sourceDataset}</p>
            )}
            {evidence.recordId && <p>Record: {evidence.recordId}</p>}
          </div>
        </details>
      )}
    </>
  );
}
