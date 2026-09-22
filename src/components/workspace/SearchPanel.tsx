import { useEffect, useRef, useState } from "react";
import type { Paper } from "../../lib/types";
import { searchPaper, type SearchResult } from "../../lib/search";

export function SearchPanel({
  paper,
  onNavigate,
  inputRef,
  onClose,
}: {
  paper: Paper;
  onNavigate: (anchor: string, term: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = window.setTimeout(() => {
      setResults(query.trim().length >= 2 ? searchPaper(paper, query) : []);
    }, 120);
    return () => window.clearTimeout(t);
  }, [query, paper]);

  return (
    <div className="border-b border-line bg-surface">
      <div className="mx-auto max-w-[1400px] px-4 py-3 md:px-5">
        <div className="mx-auto max-w-2xl">
          <label htmlFor="paper-search" className="sr-only">
            Search paper
          </label>
          <input
            ref={inputRef}
            id="paper-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose();
            }}
            placeholder="Search paper — try “transformer”, “dataset”, “accuracy”…"
            autoComplete="off"
            className="h-10 w-full rounded-[4px] border border-line bg-paper px-3 text-sm placeholder:text-secondary/70"
          />
          <div
            ref={listRef}
            role={results.length > 0 ? "listbox" : undefined}
            aria-label={results.length > 0 ? "Search results" : undefined}
            className="mt-2"
          >
            {query.trim().length >= 2 && results.length === 0 ? (
              <p className="py-2 text-[13px] text-secondary">
                No matches for “{query.trim()}” in this paper.
              </p>
            ) : null}
            {results.length > 0 ? (
              <p className="py-1 text-xs text-secondary">
                {results.length} match{results.length === 1 ? "" : "es"}
                {results.length >= 30 ? " (showing first 30)" : ""} — Esc to
                close
              </p>
            ) : null}
            <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto pb-1">
              {results.map((r) => (
                <li key={r.key}>
                  <button
                    type="button"
                    onClick={() => onNavigate(r.anchor, query.trim())}
                    className="block w-full rounded-[4px] px-2 py-2 text-left transition-colors hover:bg-muted"
                  >
                    <span className="flex items-baseline justify-between gap-3">
                      <span className="truncate text-[13px] font-medium">
                        {r.sectionLabel}
                      </span>
                      <span className="shrink-0 text-xs text-secondary">
                        {r.page}
                      </span>
                    </span>
                    <span className="mt-0.5 block text-[13px] leading-relaxed text-secondary">
                      {r.snippetBefore}
                      <mark className="rounded-[2px] bg-accent-soft px-0.5 text-ink">
                        {r.match}
                      </mark>
                      {r.snippetAfter}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
