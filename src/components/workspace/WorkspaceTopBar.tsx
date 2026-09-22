import { ArrowLeft, Menu, PanelRight, Search, X } from "lucide-react";
import { Link } from "react-router-dom";
import { cx } from "../../lib/utils";
import { BrandMark } from "../ui/BrandMark";
import { DifficultySelector } from "./DifficultySelector";

export function WorkspaceTopBar({
  title,
  onMenu,
  searchOpen,
  onSearchToggle,
  contextOpen,
  onContextToggle,
}: {
  title: string;
  onMenu: () => void;
  searchOpen: boolean;
  onSearchToggle: () => void;
  contextOpen: boolean;
  onContextToggle: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/95 backdrop-blur-[2px]">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-2 px-4 md:px-5">
        <button
          type="button"
          onClick={onMenu}
          aria-label="Open paper outline"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[4px] text-secondary transition-colors hover:bg-muted hover:text-ink lg:hidden"
        >
          <Menu className="h-[18px] w-[18px]" aria-hidden="true" />
        </button>

        <Link
          to="/"
          className="hidden shrink-0 items-center gap-2 sm:flex"
          aria-label="PaperLens home"
        >
          <BrandMark size={24} />
          <span className="text-[14.5px] font-semibold tracking-tight">
            PaperLens
          </span>
        </Link>

        <span aria-hidden="true" className="hidden h-5 w-px bg-line sm:block" />

        <Link
          to="/workspace"
          className="inline-flex shrink-0 items-center gap-1 text-[13px] font-medium text-secondary transition-colors hover:text-ink"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          Papers
        </Link>

        <p
          className="min-w-0 flex-1 truncate px-2 text-center text-[13.5px] font-medium"
          title={title}
        >
          {title}
        </p>

        <div
          className="hidden shrink-0 md:block"
          title="Explanation level will apply to AI-generated explanations in a later stage."
        >
          <DifficultySelector compact showHint={false} />
        </div>

        <button
          type="button"
          onClick={onSearchToggle}
          aria-expanded={searchOpen}
          aria-label={searchOpen ? "Close paper search" : "Search paper ( / )"}
          title="Search paper ( / )"
          className={cx(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-[4px] transition-colors",
            searchOpen
              ? "bg-accent-soft text-accent"
              : "text-secondary hover:bg-muted hover:text-ink",
          )}
        >
          {searchOpen ? (
            <X className="h-[18px] w-[18px]" aria-hidden="true" />
          ) : (
            <Search className="h-[18px] w-[18px]" aria-hidden="true" />
          )}
        </button>

        <button
          type="button"
          onClick={onContextToggle}
          aria-expanded={contextOpen}
          aria-label={contextOpen ? "Hide details panel" : "Show details panel"}
          title="Details panel"
          className={cx(
            "hidden h-9 w-9 shrink-0 items-center justify-center rounded-[4px] transition-colors xl:flex",
            contextOpen
              ? "bg-accent-soft text-accent"
              : "text-secondary hover:bg-muted hover:text-ink",
          )}
        >
          <PanelRight className="h-[18px] w-[18px]" aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
