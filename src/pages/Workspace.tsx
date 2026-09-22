import {
  BookMarked,
  FlaskConical,
  ListTree,
  ScanSearch,
  ScrollText,
  TriangleAlert,
  Database,
  BarChart3,
} from "lucide-react";
import { Footer } from "../components/layout/Footer";
import { Navbar } from "../components/layout/Navbar";
import { EmptyWorkspace } from "../components/workspace/EmptyWorkspace";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceSidebar } from "../components/workspace/WorkspaceSidebar";
import { useDocumentTitle } from "../lib/useDocumentTitle";

const PLACEHOLDER_SECTIONS = [
  { id: "overview", label: "Overview", icon: ScrollText },
  { id: "problem", label: "Problem", icon: ScanSearch },
  { id: "methodology", label: "Methodology", icon: FlaskConical },
  { id: "dataset", label: "Dataset", icon: Database },
  { id: "results", label: "Results", icon: BarChart3 },
  { id: "limitations", label: "Limitations", icon: TriangleAlert },
  { id: "research-gap", label: "Research Gap", icon: ListTree },
  { id: "references", label: "References", icon: BookMarked },
];

/** Empty workspace shell at /workspace (no paper selected). */
export function Workspace() {
  useDocumentTitle("Workspace — PaperLens");
  return (
    <div className="page-enter flex min-h-screen flex-col">
      <Navbar />
      <WorkspaceHeader />
      <div className="mx-auto flex w-full max-w-6xl flex-1 items-stretch gap-0 px-0 md:gap-6 md:px-5 md:py-6">
        <aside className="thin-scroll sticky top-14 hidden max-h-[calc(100vh-3.5rem)] w-60 shrink-0 overflow-y-auto border-r border-line bg-surface px-3 py-4 md:block">
          <WorkspaceSidebar
            primary={PLACEHOLDER_SECTIONS}
            disabled
            disabledNote="Sections become available once a paper is added."
          />
        </aside>

        <main className="min-w-0 flex-1 bg-paper px-5 py-6 md:rounded-[4px] md:border md:border-line md:bg-surface md:px-7">
          <div className="mb-5 md:hidden">
            <WorkspaceSidebar
              mobile
              primary={PLACEHOLDER_SECTIONS}
              disabled
              disabledNote="Sections unlock after a paper is added."
            />
          </div>
          <EmptyWorkspace />
        </main>
      </div>
      <Footer />
    </div>
  );
}
