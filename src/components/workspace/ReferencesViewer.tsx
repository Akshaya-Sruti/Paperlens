import { useEffect, useRef } from "react";
import type { PaperReference } from "../../lib/types";
import { cx } from "../../lib/utils";

export function ReferencesViewer({
  references,
  highlightIndex = null,
}: {
  references: PaperReference[];
  highlightIndex?: number | null;
}) {
  const highlightRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (highlightIndex != null) {
      highlightRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [highlightIndex]);

  return (
    <div>
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        {references.length} {references.length === 1 ? "entry" : "entries"} ·
        parsed where possible
      </p>
      <h2 className="mt-1 font-serif text-[22px] font-medium tracking-tight">
        References
      </h2>
      <ol className="mt-5 flex max-w-3xl flex-col gap-3">
        {references.map((ref) => {
          const key = ref.index ?? ref.raw_text.slice(0, 40);
          const highlighted =
            highlightIndex != null && ref.index === highlightIndex;
          return (
            <li
              key={key}
              ref={highlighted ? highlightRef : undefined}
              className={cx(
                "rounded-[4px] border px-4 py-3 transition-colors duration-300",
                highlighted
                  ? "border-accent/50 bg-accent-soft"
                  : "border-line bg-paper",
              )}
            >
              <div className="flex gap-3">
                <span className="shrink-0 font-mono text-xs text-secondary">
                  {ref.index != null
                    ? String(ref.index).padStart(2, "0")
                    : "—"}
                </span>
                <div className="min-w-0">
                  <p className="text-[13.5px] leading-relaxed">{ref.raw_text}</p>
                  {(ref.authors.length > 0 || ref.title || ref.year || ref.doi) && (
                    <dl className="mt-2 flex flex-col gap-0.5 border-t border-line pt-2 text-xs text-secondary">
                      {ref.title ? (
                        <div className="flex gap-2">
                          <dt className="w-14 shrink-0">Title</dt>
                          <dd className="text-ink">{ref.title}</dd>
                        </div>
                      ) : null}
                      {ref.authors.length > 0 ? (
                        <div className="flex gap-2">
                          <dt className="w-14 shrink-0">Authors</dt>
                          <dd>{ref.authors.join(", ")}</dd>
                        </div>
                      ) : null}
                      {ref.year ? (
                        <div className="flex gap-2">
                          <dt className="w-14 shrink-0">Year</dt>
                          <dd>{ref.year}</dd>
                        </div>
                      ) : null}
                      {ref.doi ? (
                        <div className="flex gap-2">
                          <dt className="w-14 shrink-0">DOI</dt>
                          <dd>
                            <a
                              href={`https://doi.org/${ref.doi}`}
                              target="_blank"
                              rel="noreferrer"
                              className="font-medium text-accent underline underline-offset-2"
                            >
                              {ref.doi}
                            </a>
                          </dd>
                        </div>
                      ) : null}
                    </dl>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-4 text-xs text-secondary">
        Fields appear only when extraction is reliable — the raw text is
        always preserved.
      </p>
    </div>
  );
}
