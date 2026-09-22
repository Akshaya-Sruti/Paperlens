import { ScanLine } from "lucide-react";

export function ScannedNotice() {
  return (
    <div
      role="note"
      className="mb-6 flex gap-3 rounded-[4px] border border-line bg-muted px-4 py-3"
    >
      <ScanLine
        className="mt-0.5 h-4 w-4 shrink-0 text-secondary"
        aria-hidden="true"
      />
      <p className="text-[13px] leading-relaxed text-secondary">
        <span className="font-medium text-ink">Scanned pages detected. </span>
        This paper appears to contain scanned pages rather than selectable
        text. OCR support will be added in a future version.
      </p>
    </div>
  );
}
