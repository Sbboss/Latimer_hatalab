import type { EvidenceQuestion } from "../lib/types";

type Props = {
  evidence: EvidenceQuestion;
  dark?: boolean;
};

export function ResponseDataNotice({ evidence, dark = false }: Props) {
  const missingWaves = evidence.responseDataMissingWaves ?? evidence.availableWaves ?? [];

  return (
    <div
      className={`response-data-notice${dark ? " response-data-notice-dark" : ""}`}
      aria-label="Response distribution unavailable"
    >
      <strong>Response distribution unavailable</strong>
      <p>
        The official record preserves this question and its study coverage, but no
        verified response distribution is available. No opinion trend is inferred.
      </p>
      <dl>
        <div>
          <dt>Source</dt>
          <dd>{evidence.sourceDataset || "Official survey record"}</dd>
        </div>
        <div>
          <dt>Affected waves</dt>
          <dd>{missingWaves.length ? missingWaves.join(", ") : "Unspecified"}</dd>
        </div>
      </dl>
    </div>
  );
}
