import { FileUp } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../ui/Button";

export function EmptyWorkspace() {
  return (
    <div className="flex flex-col items-center px-6 py-16 text-center md:py-20">
      <span className="flex h-11 w-11 items-center justify-center rounded-[4px] border border-line bg-muted text-secondary">
        <FileUp className="h-5 w-5" aria-hidden="true" />
      </span>
      <h2 className="mt-5 font-serif text-[22px] font-medium tracking-tight">
        No paper in the workspace
      </h2>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-secondary">
        The workspace is waiting for a paper. Add a PDF to stage it here —
        structured understanding arrives in later stages.
      </p>
      <Link to="/upload" className="mt-6">
        <Button>
          <FileUp className="h-4 w-4" aria-hidden="true" />
          Upload paper
        </Button>
      </Link>
      <p className="mt-4 text-xs text-secondary">
        PDF only · up to 20 MB · stays in your browser for now
      </p>
    </div>
  );
}
