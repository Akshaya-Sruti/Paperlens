import { useEffect, useRef } from "react";
import type { Paper } from "../../lib/types";
import { RawTextViewer } from "./RawTextViewer";

export function RawTextModal({
  paper,
  onClose,
}: {
  paper: Paper;
  onClose: () => void;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<Element | null>(null);

  useEffect(() => {
    previousFocus.current = document.activeElement;
    closeRef.current?.focus();
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      (previousFocus.current as HTMLElement | null)?.focus?.();
    };
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Extracted text"
      className="fixed inset-0 z-50 flex items-stretch justify-center bg-ink/40 p-0 sm:items-center sm:p-6"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-full w-full max-w-3xl flex-col overflow-hidden bg-surface sm:max-h-[85vh] sm:rounded-[4px] sm:border sm:border-line">
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">
              Extracted text
            </p>
            <p className="text-xs text-secondary">
              Exactly what PaperLens read — nothing added, nothing rewritten.
            </p>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close extracted text"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[4px] text-secondary transition-colors hover:bg-muted hover:text-ink"
          >
            <span aria-hidden="true" className="text-xl leading-none">
              ×
            </span>
          </button>
        </div>
        <div className="thin-scroll overflow-y-auto px-5 py-5">
          <RawTextViewer pages={paper.pages} />
        </div>
      </div>
    </div>
  );
}
