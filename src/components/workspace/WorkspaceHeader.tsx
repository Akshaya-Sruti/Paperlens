import { FileText } from "lucide-react";
import { usePaper } from "../../lib/paper-context";
import { formatBytes } from "../../lib/utils";
import type { Paper } from "../../lib/types";
import { DifficultySelector } from "./DifficultySelector";

export function WorkspaceHeader({ paper }: { paper?: Paper | null }) {
  const { stagedMeta } = usePaper();

  const title = paper?.title ?? stagedMeta?.name ?? "Your paper workspace";
  const subtitle = paper
    ? byline(paper)
    : stagedMeta
      ? "Staged locally. Processing arrives in a later stage."
      : "Upload a research paper to begin.";

  return (
    <div className="border-b border-line bg-surface">
      <div className="flex flex-col gap-4 px-5 py-4 md:flex-row md:items-end md:justify-between md:px-7">
        <div className="min-w-0">
          <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
            Paper workspace
          </p>
          <div className="mt-1.5 flex min-w-0 items-center gap-2">
            {(paper || stagedMeta) && (
              <FileText
                className="h-4 w-4 shrink-0 text-accent"
                aria-hidden="true"
              />
            )}
            <h1 className="truncate text-[17px] font-semibold tracking-tight" title={title}>
              {title}
            </h1>
            {paper ? (
              <span className="shrink-0 text-xs text-secondary">
                · {paper.page_count} {paper.page_count === 1 ? "page" : "pages"}
              </span>
            ) : stagedMeta ? (
              <span className="shrink-0 text-xs text-secondary">
                · {formatBytes(stagedMeta.size)}
              </span>
            ) : null}
          </div>
          <p className="mt-0.5 truncate text-[13px] text-secondary">{subtitle}</p>
        </div>
        <DifficultySelector compact />
      </div>
    </div>
  );
}

function byline(paper: Paper): string {
  const parts: string[] = [];
  const names = paper.authors.map((a) => a.name);
  if (names.length > 0) {
    parts.push(
      names.slice(0, 3).join(", ") +
        (names.length > 3 ? ` +${names.length - 3} more` : ""),
    );
  }
  if (paper.publication.venue) parts.push(paper.publication.venue);
  else if (paper.year) parts.push(String(paper.year));
  return parts.join(" · ") || paper.filename;
}
