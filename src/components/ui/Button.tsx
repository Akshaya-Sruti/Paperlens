import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../../lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "quiet";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-white border-accent hover:bg-accent-dark disabled:bg-muted disabled:text-secondary disabled:border-line",
  secondary:
    "bg-surface text-ink border-line hover:border-secondary/50 hover:bg-muted/60 disabled:opacity-50",
  ghost: "bg-transparent text-ink border-transparent hover:bg-muted",
  quiet:
    "bg-transparent text-secondary border-transparent hover:text-ink hover:bg-muted",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px]",
  md: "h-10 px-4 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cx(
        "inline-flex cursor-pointer items-center justify-center gap-2 rounded-[4px] border font-medium transition-colors duration-150 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
