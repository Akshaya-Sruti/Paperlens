import { FileText, X } from "lucide-react";
import { formatBytes } from "../../lib/utils";

interface FilePreviewProps {
  name: string;
  size: number;
  onRemove: () => void;
  disabled?: boolean;
}

export function FilePreview({ name, size, onRemove, disabled = false }: FilePreviewProps) {
  return (
    <div
      className="flex items-center gap-3 rounded-[4px] border border-line bg-surface px-4 py-3"
      aria-live="polite"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[3px] bg-accent-soft text-accent">
        <FileText className="h-[18px] w-[18px]" aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium" title={name}>
          {name}
        </p>
        <p className="text-xs text-secondary">
          PDF · {formatBytes(size)}
        </p>
      </div>
      <button
        type="button"
        onClick={onRemove}
        disabled={disabled}
        aria-label={`Remove ${name}`}
        className="inline-flex h-8 items-center gap-1.5 rounded-[4px] border border-line bg-surface px-2.5 text-[13px] font-medium text-secondary transition-colors duration-150 hover:border-secondary/40 hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
      >
        <X className="h-3.5 w-3.5" aria-hidden="true" />
        Remove
      </button>
    </div>
  );
}
