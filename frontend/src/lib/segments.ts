import type { Highlight } from "./types";

export type Segment =
  | { kind: "text"; text: string }
  | { kind: "highlight"; text: string; id: string };

// Build a render-ready segment list from raw text and highlights.
// Robust to overlap; falls back to phrase indexOf if start/end are missing
// or out of range (e.g. when the upstream model returns approximate spans).
export function buildSegments(text: string, highlights: Highlight[]): Segment[] {
  if (!text) return [];

  const positioned = highlights
    .map((h) => {
      const start =
        Number.isInteger(h.start) && h.start >= 0 && h.start < text.length
          ? h.start
          : text.indexOf(h.phrase);
      const end =
        Number.isInteger(h.end) && h.end > start && h.end <= text.length
          ? h.end
          : start >= 0
          ? start + h.phrase.length
          : -1;
      return { h, start, end };
    })
    .filter((p) => p.start >= 0 && p.end > p.start)
    .sort((a, b) => a.start - b.start);

  const segments: Segment[] = [];
  let cursor = 0;
  for (const { h, start, end } of positioned) {
    if (start < cursor) continue; // skip overlap
    if (start > cursor) segments.push({ kind: "text", text: text.slice(cursor, start) });
    segments.push({ kind: "highlight", text: text.slice(start, end), id: h.id });
    cursor = end;
  }
  if (cursor < text.length) {
    segments.push({ kind: "text", text: text.slice(cursor) });
  }
  return segments;
}
