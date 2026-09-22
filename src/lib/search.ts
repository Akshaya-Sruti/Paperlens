import type { Paper } from "./types";

export interface SearchResult {
  key: string;
  /** Anchor id to scroll to: `sec-<sectionId>`, `abstract`, `references`, `figures`. */
  anchor: string;
  sectionLabel: string;
  page: string;
  snippetBefore: string;
  match: string;
  snippetAfter: string;
}

const SNIPPET_RADIUS = 70;
const MAX_RESULTS = 30;

function makeSnippet(
  text: string,
  index: number,
  termLength: number,
): { snippetBefore: string; match: string; snippetAfter: string } {
  const clean = text.replace(/\s+/g, " ");
  const start = Math.max(0, index - SNIPPET_RADIUS);
  const end = Math.min(clean.length, index + termLength + SNIPPET_RADIUS);
  return {
    snippetBefore: (start > 0 ? "…" : "") + clean.slice(start, index),
    match: clean.slice(index, index + termLength),
    snippetAfter:
      clean.slice(index + termLength, end) + (end < clean.length ? "…" : ""),
  };
}

function pageLabel(start: number, end: number): string {
  return start === end ? `p. ${start}` : `pp. ${start}–${end}`;
}

/** Local full-text search over extracted paper content. No AI involved. */
export function searchPaper(paper: Paper, query: string): SearchResult[] {
  const term = query.trim().toLowerCase();
  if (term.length < 2) return [];
  const results: SearchResult[] = [];

  const pushHit = (args: {
    key: string;
    anchor: string;
    sectionLabel: string;
    page: string;
    haystack: string;
  }) => {
    if (results.length >= MAX_RESULTS) return;
    const lower = args.haystack.toLowerCase();
    const at = lower.indexOf(term);
    if (at === -1) return;
    const snippet = makeSnippet(args.haystack, at, term.length);
    results.push({
      key: args.key,
      anchor: args.anchor,
      sectionLabel: args.sectionLabel,
      page: args.page,
      ...snippet,
    });
  };

  if (paper.abstract) {
    pushHit({
      key: "abstract",
      anchor: "abstract",
      sectionLabel: "Abstract",
      page: "p. 1",
      haystack: paper.abstract,
    });
  }

  for (const section of paper.sections) {
    if (results.length >= MAX_RESULTS) break;
    const haystack = `${section.title}\n${section.content}`;
    const lower = haystack.toLowerCase();
    let from = 0;
    let count = 0;
    for (;;) {
      const at = lower.indexOf(term, from);
      if (at === -1 || count >= 2) break;
      const snippet = makeSnippet(haystack, at, term.length);
      results.push({
        key: `${section.id}-${count}`,
        anchor: `sec-${section.id}`,
        sectionLabel:
          (section.number ? `${section.number} ` : "") + section.title,
        page: pageLabel(section.start_page, section.end_page),
        ...snippet,
      });
      from = at + term.length;
      count += 1;
      if (results.length >= MAX_RESULTS) break;
    }
  }

  if (results.length < MAX_RESULTS) {
    for (const ref of paper.references) {
      if (results.length >= MAX_RESULTS) break;
      pushHit({
        key: `ref-${ref.index ?? ref.raw_text.slice(0, 20)}`,
        anchor: "references",
        sectionLabel:
          ref.index != null ? `Reference ${ref.index}` : "References",
        page: "references",
        haystack: ref.raw_text,
      });
    }
  }

  return results;
}
