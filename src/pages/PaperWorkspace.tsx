import { ArrowLeft, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Footer } from "../components/layout/Footer";
import { Button } from "../components/ui/Button";
import { ContextPanel } from "../components/workspace/ContextPanel";
import { DifficultySelector } from "../components/workspace/DifficultySelector";
import { DocumentView } from "../components/workspace/DocumentView";
import { RawTextModal } from "../components/workspace/RawTextModal";
import { SearchPanel } from "../components/workspace/SearchPanel";
import { WorkspaceSidebar } from "../components/workspace/WorkspaceSidebar";
import { WorkspaceTopBar } from "../components/workspace/WorkspaceTopBar";
import { buildPaperNav } from "../components/workspace/paperNav";
import { ApiError, getPaper } from "../lib/api";
import type { Paper } from "../lib/types";
import { useDocumentTitle } from "../lib/useDocumentTitle";
import { pageRangeLabel } from "../components/workspace/SectionBlock";

export function PaperWorkspace() {
  const { paperId = "" } = useParams();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string>("overview");
  const [refHighlight, setRefHighlight] = useState<number | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [highlight, setHighlight] = useState<{
    term: string;
    anchor: string;
  } | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);
  const [rawOpen, setRawOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const drawerCloseRef = useRef<HTMLButtonElement>(null);

  useDocumentTitle(
    paper ? `${paper.title ?? paper.filename} — PaperLens` : "Paper — PaperLens",
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPaper(null);
    setActive("overview");
    setRefHighlight(null);
    setHighlight(null);
    setSearchOpen(false);
    setRawOpen(false);
    getPaper(paperId)
      .then((p) => {
        if (!cancelled) {
          setPaper(p);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Could not load this paper. Try uploading it again.",
          );
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [paperId]);

  const nav = useMemo(
    () =>
      paper
        ? buildPaperNav(
            paper.sections,
            paper.references.length,
            paper.figures.length + paper.tables.length,
          )
        : null,
    [paper],
  );

  const scrollToAnchor = useCallback((anchor: string) => {
    const el = document.getElementById(anchor);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  // Scrollspy: track the section currently in view.
  useEffect(() => {
    if (!paper) return;
    const elements = Array.from(
      document.querySelectorAll<HTMLElement>("[data-spy]"),
    );
    if (elements.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort(
            (a, b) =>
              (a.target as HTMLElement).offsetTop -
              (b.target as HTMLElement).offsetTop,
          );
        if (visible.length > 0) {
          const key = visible[0].target.getAttribute("data-spy");
          if (key) setActive(key);
        }
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 },
    );
    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [paper]);

  const navigate = useCallback(
    (id: string) => {
      if (id === "raw") {
        setRawOpen(true);
        setDrawerOpen(false);
        return;
      }
      setRefHighlight(null);
      setActive(id);
      setDrawerOpen(false);
      const anchor =
        id === "overview"
          ? "top"
          : id === "figures"
            ? "figures"
            : id === "references"
              ? "references"
              : id.startsWith("section:")
                ? `sec-${id.replace(/^section:/, "")}`
                : "top";
      // Abstract lives in the overview block.
      const sectionId = id.replace(/^section:/, "");
      const section = paper?.sections.find((s) => s.id === sectionId);
      scrollToAnchor(
        section?.normalized_type === "abstract" ? "abstract" : anchor,
      );
    },
    [paper, scrollToAnchor],
  );

  const openReference = useCallback(
    (index: number) => {
      setRefHighlight(index);
      setActive("references");
      scrollToAnchor("references");
    },
    [scrollToAnchor],
  );

  const searchNavigate = useCallback(
    (anchor: string, term: string) => {
      setHighlight({ term, anchor });
      setRefHighlight(null);
      scrollToAnchor(anchor);
      setSearchOpen(false);
    },
    [scrollToAnchor],
  );

  // Keyboard: "/" opens search when not typing; Esc closes the drawer.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const typing =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);
      if (e.key === "/" && !typing && !searchOpen && paper) {
        e.preventDefault();
        setSearchOpen(true);
      } else if (e.key === "Escape" && drawerOpen) {
        setDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [searchOpen, drawerOpen, paper]);

  useEffect(() => {
    if (searchOpen) {
      const t = window.setTimeout(() => searchInputRef.current?.focus(), 30);
      return () => window.clearTimeout(t);
    }
  }, [searchOpen]);

  useEffect(() => {
    if (drawerOpen) {
      drawerCloseRef.current?.focus();
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = "";
      };
    }
  }, [drawerOpen]);

  const currentSection = useMemo(() => {
    if (!paper || active === "overview") return null;
    if (active === "references")
      return {
        title: "References",
        pages: `${paper.references.length} entries`,
      };
    if (active === "figures")
      return { title: "Figures & Tables", pages: "Detected items" };
    const section = paper.sections.find(
      (s) => `section:${s.id}` === active || s.id === active,
    );
    if (!section) return null;
    return {
      title: (section.number ? `${section.number} ` : "") + section.title,
      pages: pageRangeLabel(section.start_page, section.end_page),
    };
  }, [paper, active]);

  const title = paper?.title ?? paper?.filename ?? "Paper";

  return (
    <div className="page-enter flex min-h-screen flex-col">
      <WorkspaceTopBar
        title={title}
        onMenu={() => setDrawerOpen(true)}
        searchOpen={searchOpen}
        onSearchToggle={() => setSearchOpen((v) => !v)}
        contextOpen={contextOpen}
        onContextToggle={() => setContextOpen((v) => !v)}
      />

      {searchOpen && paper ? (
        <SearchPanel
          paper={paper}
          onNavigate={searchNavigate}
          inputRef={searchInputRef}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}

      <div className="mx-auto flex w-full max-w-[1400px] flex-1 items-stretch gap-0 px-0 lg:gap-6 lg:px-5 lg:py-6">
        <aside className="thin-scroll sticky top-14 hidden max-h-[calc(100vh-3.5rem)] w-60 shrink-0 overflow-y-auto border-r border-line bg-surface px-3 py-4 lg:block">
          {paper && nav ? (
            <WorkspaceSidebar
              primary={[]}
              groups={nav.groups}
              activeId={active}
              onNavigate={navigate}
            />
          ) : (
            <WorkspaceSidebar
              primary={[]}
              disabled
              disabledNote="Sections will appear here once the paper loads."
            />
          )}
        </aside>

        <main className="min-w-0 flex-1 bg-paper px-5 py-6 sm:px-8 md:py-8 lg:rounded-[4px] lg:border lg:border-line lg:bg-surface lg:px-10">
          {loading ? (
            <LoadingState />
          ) : error || !paper ? (
            <ErrorState message={error ?? "Could not load this paper."} />
          ) : (
            <DocumentView
              paper={paper}
              highlightTerm={highlight?.term ?? null}
              highlightAnchor={highlight?.anchor ?? null}
              refHighlight={refHighlight}
              onCitationClick={openReference}
            />
          )}
        </main>

        {paper && !loading && !error ? (
          <ContextPanel
            paper={paper}
            currentSection={currentSection}
            open={contextOpen}
            onClose={() => setContextOpen(false)}
          />
        ) : null}
      </div>

      {drawerOpen && paper && nav ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Paper outline"
          className="fixed inset-0 z-50 lg:hidden"
        >
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-ink/40"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="thin-scroll absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col overflow-y-auto border-r border-line bg-surface px-3 py-4">
            <div className="mb-2 flex items-center justify-between px-2">
              <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
                Outline
              </p>
              <button
                ref={drawerCloseRef}
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close outline"
                className="flex h-8 w-8 items-center justify-center rounded-[4px] text-secondary transition-colors hover:bg-muted hover:text-ink"
              >
                <span aria-hidden="true" className="text-lg leading-none">
                  ×
                </span>
              </button>
            </div>
            <WorkspaceSidebar
              primary={[]}
              groups={nav.groups}
              activeId={active}
              onNavigate={navigate}
            />
            <div className="mt-4 border-t border-line px-2 pt-4">
              <DifficultySelector />
              <p className="mt-2 text-xs leading-relaxed text-secondary">
                Applies to AI explanations later — extracted text never
                changes.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {rawOpen && paper ? (
        <RawTextModal paper={paper} onClose={() => setRawOpen(false)} />
      ) : null}

      <Footer />
    </div>
  );
}

function LoadingState() {
  return (
    <div
      className="mx-auto flex w-full max-w-2xl flex-col py-14"
      role="status"
      aria-label="Loading paper"
    >
      <p className="font-serif text-xl font-medium tracking-tight">
        Loading paper
      </p>
      <p className="mt-1 text-sm text-secondary">
        Preparing document structure…
      </p>
      <div className="mt-6 flex flex-col gap-4" aria-hidden="true">
        {[72, 45, 90, 60].map((width, i) => (
          <div
            key={i}
            className="h-3.5 animate-pulse rounded-[2px] bg-muted"
            style={{ width: `${width}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center px-6 py-16 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-[4px] border border-accent/30 bg-accent-soft text-accent">
        <TriangleAlert className="h-5 w-5" aria-hidden="true" />
      </span>
      <h1 className="mt-5 font-serif text-[22px] font-medium tracking-tight">
        Unable to load this paper
      </h1>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-secondary">
        {message}
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link to="/upload">
          <Button>Upload a paper</Button>
        </Link>
        <Link
          to="/workspace"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-secondary transition-colors hover:text-ink"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Return to your papers
        </Link>
      </div>
    </div>
  );
}
