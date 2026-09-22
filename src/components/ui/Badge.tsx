import { cx } from "../../lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "accent" | "outline";
  className?: string;
}) {
  const tones: Record<string, string> = {
    neutral: "bg-muted text-secondary border-line",
    accent: "bg-accent-soft text-accent border-accent/20",
    outline: "bg-transparent text-secondary border-line",
  };
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-[3px] border px-1.5 py-0.5 text-[11px] font-medium tracking-wide uppercase",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
