import type { Highlight } from "../lib/types";
import { buildSegments } from "../lib/segments";

type Props = {
  text: string;
  highlights: Highlight[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function HighlightedText({ text, highlights, selectedId, onSelect }: Props) {
  const segments = buildSegments(text, highlights);

  if (highlights.length === 0) {
    return (
      <p className="editor-text">
        {text}
      </p>
    );
  }

  return (
    <div>
      <p className="highlight-action-hint">
        Underlined signals open their Insight Board <span aria-hidden>↓</span>
      </p>
      <p className="editor-text">
        {segments.map((seg, i) => {
          if (seg.kind === "text") {
            return <span key={i}>{seg.text}</span>;
          }
          const isSelected = seg.id === selectedId;
          return (
            <button
              key={i}
              type="button"
              className={`hl-mark ${isSelected ? "is-selected" : ""}`}
              onClick={() => onSelect(seg.id)}
              aria-pressed={isSelected}
              aria-label={`Open “${seg.text}” in the Insight Board`}
              title="Open this signal in the Insight Board"
            >
              {seg.text}<span className="hl-open-mark" aria-hidden>↘</span>
            </button>
          );
        })}
      </p>
    </div>
  );
}
