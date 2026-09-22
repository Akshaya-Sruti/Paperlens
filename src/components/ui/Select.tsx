import { ChevronDown } from "lucide-react";
import type { SelectHTMLAttributes } from "react";
import { cx } from "../../lib/utils";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  hint?: string;
  /** Visually hide the label (kept for screen readers) — for dense bars. */
  slim?: boolean;
}

export function Select({ label, hint, slim = false, className, id, children, ...rest }: SelectProps) {
  const selectId = id ?? "select-control";
  return (
    <div className={cx("flex flex-col gap-1", className)}>
      <label
        htmlFor={selectId}
        className={
          slim
            ? "sr-only"
            : "text-[11px] font-medium tracking-wide text-secondary uppercase"
        }
      >
        {label}
      </label>
      <div className="relative">
        <select
          id={selectId}
          className="h-9 w-full cursor-pointer appearance-none rounded-[4px] border border-line bg-surface pr-8 pl-3 text-sm text-ink transition-colors duration-150 hover:border-secondary/40"
          {...rest}
        >
          {children}
        </select>
        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 right-2.5 h-4 w-4 -translate-y-1/2 text-secondary"
        />
      </div>
      {hint ? <p className="text-xs text-secondary">{hint}</p> : null}
    </div>
  );
}
