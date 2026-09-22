import type { ReactNode } from "react";
import { cx } from "../../lib/utils";

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "rounded-[4px] border border-line bg-surface",
        "shadow-[0_1px_2px_rgba(23,23,23,0.04)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("border-b border-line px-5 py-3.5", className)}>
      {children}
    </div>
  );
}

export function CardBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx("px-5 py-4", className)}>{children}</div>;
}
