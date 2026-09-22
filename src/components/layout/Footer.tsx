import { Link } from "react-router-dom";
import { BrandMark } from "../ui/BrandMark";

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-8 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2.5">
          <BrandMark size={22} />
          <div>
            <p className="text-sm font-semibold tracking-tight">PaperLens</p>
            <p className="mt-0.5 text-[13px] text-secondary">
              Understand research. Your way.
            </p>
          </div>
        </div>
        <nav
          className="flex items-center gap-5 text-[13px] text-secondary"
          aria-label="Footer"
        >
          <Link to="/upload" className="transition-colors hover:text-ink">
            Upload
          </Link>
          <Link to="/workspace" className="transition-colors hover:text-ink">
            Workspace
          </Link>
          <span className="text-secondary/70">Stage 1 — Foundation</span>
        </nav>
      </div>
    </footer>
  );
}
