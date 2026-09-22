import type { Paper } from "../../lib/types";
import { usePaper } from "../../lib/paper-context";
import { EXPLANATION_LEVELS } from "../../lib/paper-context";
import { DifficultySelector } from "./DifficultySelector";

export function ContextPanel({
  paper,
  currentSection,
  open,
  onClose,
}: {
  paper: Paper;
  currentSection: { title: string; pages: string } | null;
  open: boolean;
  onClose: () => void;
}) {
  const { explanationLevel } = usePaper();
  const levelHint =
    EXPLANATION_LEVELS.find((l) => l.value === explanationLevel)?.hint ?? "";

  if (!open) return null;

  const rows: Array<[string, string]> = [
    ["Pages", String(paper.page_count)],
    ["Sections", String(paper.sections.length)],
    ["References", String(paper.references.length)],
    ["Figures", String(paper.figures.length)],
    ["Tables", String(paper.tables.length)],
    ["Citations", String(paper.citations.length)],
  ];

  return (
    <aside
      aria-label="Paper details"
      className="thin-scroll sticky top-14 hidden max-h-[calc(100vh-3.5rem)] w-64 shrink-0 overflow-y-auto border-l border-line bg-surface px-4 py-5 xl:block"
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
          Paper information
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label="Hide details panel"
          className="rounded-[4px] px-1.5 py-0.5 text-xs text-secondary transition-colors hover:bg-muted hover:text-ink"
        >
          Hide
        </button>
      </div>
      <dl className="mt-3 flex flex-col gap-1.5">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-baseline justify-between gap-3 text-[13px]">
            <dt className="text-secondary">{label}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 border-t border-line pt-4">
        <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
          Currently reading
        </p>
        {currentSection ? (
          <div className="mt-2">
            <p className="text-sm font-medium">{currentSection.title}</p>
            <p className="mt-0.5 text-xs text-secondary">{currentSection.pages}</p>
          </div>
        ) : (
          <p className="mt-2 text-[13px] text-secondary">Overview</p>
        )}
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
          Explanation level
        </p>
        <div className="mt-2">
          <DifficultySelector />
        </div>
        <p className="mt-2 text-xs leading-relaxed text-secondary">
          {levelHint && `${levelHint}. `}
          Applies to AI-generated explanations in a later stage — the
          extracted text above never changes.
        </p>
      </div>
    </aside>
  );
}
