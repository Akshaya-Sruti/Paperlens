import {
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  TriangleAlert,
} from "lucide-react";
import { useCallback, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Footer } from "../components/layout/Footer";
import { Navbar } from "../components/layout/Navbar";
import { Button } from "../components/ui/Button";
import { FilePreview } from "../components/upload/FilePreview";
import { UploadDropzone } from "../components/upload/UploadDropzone";
import { ApiError, getPaper, uploadPaper } from "../lib/api";
import { usePaper } from "../lib/paper-context";
import { useDocumentTitle } from "../lib/useDocumentTitle";
import { validatePdfFile } from "../lib/utils";
import { cx } from "../lib/utils";

type UploadState = "idle" | "ready" | "busy" | "error";

interface Step {
  id: string;
  label: string;
  detail: string;
}

const STEPS: Step[] = [
  { id: "send", label: "Uploading PDF", detail: "Sending the file to the server" },
  { id: "read", label: "Reading paper", detail: "Extracting pages and text" },
  { id: "organize", label: "Organizing sections", detail: "Detecting structure" },
];

export function Upload() {
  useDocumentTitle("Upload Paper — PaperLens");
  const navigate = useNavigate();
  const { stagedFile, setStagedFile, clearStagedFile } = usePaper();
  const [state, setState] = useState<UploadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState(0);

  const handleFileAccepted = useCallback(
    (file: File) => {
      const message = validatePdfFile(file);
      if (message) {
        setError(message);
        setState("idle");
        return;
      }
      setError(null);
      setStagedFile(file);
      setState("ready");
      setCompletedSteps(0);
    },
    [setStagedFile],
  );

  const handleRemove = useCallback(() => {
    clearStagedFile();
    setError(null);
    setState("idle");
    setCompletedSteps(0);
  }, [clearStagedFile]);

  const handleUpload = useCallback(async () => {
    if (!stagedFile || state === "busy") return;
    setState("busy");
    setError(null);
    setCompletedSteps(0);
    try {
      const result = await uploadPaper(stagedFile);
      // The server responds only after extraction finished, so the first
      // two milestones are genuinely complete at this point.
      setCompletedSteps(2);
      // Confirm the structured paper is retrievable before navigating.
      await getPaper(result.paper_id);
      setCompletedSteps(3);
      navigate(`/workspace/${result.paper_id}`);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Unable to process this PDF. Try another file.";
      setError(message);
      setState("error");
    }
  }, [navigate, stagedFile, state]);

  const busy = state === "busy";

  return (
    <div className="page-enter flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-2xl px-5 py-10 md:py-14">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-secondary transition-colors hover:text-ink"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            Back to home
          </Link>

          <h1 className="mt-4 font-serif text-3xl font-medium tracking-tight">
            Upload a research paper
          </h1>
          <p className="mt-2 text-[15px] text-secondary">
            PDF files up to 20 MB. The paper is processed by the local
            PaperLens server into structured, navigable data.
          </p>

          <div className="mt-8 flex flex-col gap-4">
            {!stagedFile ? (
              <UploadDropzone
                onFileAccepted={handleFileAccepted}
                onError={setError}
                error={state === "idle" ? error : null}
              />
            ) : (
              <>
                <FilePreview
                  name={stagedFile.name}
                  size={stagedFile.size}
                  onRemove={handleRemove}
                  disabled={busy}
                />

                {busy || state === "error" ? (
                  <ProcessingSteps
                    completed={completedSteps}
                    failed={state === "error"}
                  />
                ) : null}

                {error && state !== "idle" ? (
                  <div
                    role="alert"
                    className="flex gap-3 rounded-[4px] border border-accent/30 bg-accent-soft px-4 py-3"
                  >
                    <TriangleAlert
                      className="mt-0.5 h-4 w-4 shrink-0 text-accent"
                      aria-hidden="true"
                    />
                    <div>
                      <p className="text-sm font-medium text-ink">
                        Unable to process this PDF.
                      </p>
                      <p className="mt-0.5 text-[13px] text-secondary">
                        {error}
                      </p>
                    </div>
                  </div>
                ) : null}

                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                  {state === "error" ? (
                    <Button
                      variant="secondary"
                      onClick={handleRemove}
                      className="w-full sm:w-auto"
                    >
                      Try another PDF
                    </Button>
                  ) : null}
                  <Button
                    onClick={handleUpload}
                    disabled={busy}
                    className="w-full sm:w-auto"
                  >
                    {busy ? (
                      <>
                        <Loader2
                          className="h-4 w-4 animate-spin"
                          aria-hidden="true"
                        />
                        Processing…
                      </>
                    ) : state === "error" ? (
                      <>
                        Retry upload
                        <ArrowRight className="h-4 w-4" aria-hidden="true" />
                      </>
                    ) : (
                      <>
                        Upload and continue
                        <ArrowRight className="h-4 w-4" aria-hidden="true" />
                      </>
                    )}
                  </Button>
                </div>
                {!busy && state !== "error" ? (
                  <p className="text-xs text-secondary sm:text-right">
                    Upload sends the file to the PaperLens server for
                    extraction. No AI is involved at this stage.
                  </p>
                ) : null}
              </>
            )}
          </div>

          <div className="mt-10 border-t border-line pt-5">
            <h2 className="text-[13px] font-semibold">What happens next</h2>
            <ol className="mt-2 flex flex-col gap-1.5 text-[13px] text-secondary">
              <li>1. The PDF is sent to the PaperLens server.</li>
              <li>2. Pages, metadata and sections are extracted.</li>
              <li>3. The workspace opens with the real paper structure.</li>
            </ol>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function ProcessingSteps({
  completed,
  failed,
}: {
  completed: number;
  failed: boolean;
}) {
  return (
    <ol
      className="rounded-[4px] border border-line bg-surface px-4 py-3"
      aria-live="polite"
      aria-label="Processing progress"
    >
      {STEPS.map((step, i) => {
        const done = i < completed;
        const active = !failed && i === completed;
        return (
          <li key={step.id} className="flex items-center gap-3 py-1.5">
            <span
              className={cx(
                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",
                done && "border-accent bg-accent text-white",
                active && "border-accent",
                failed && i === completed && "border-accent",
                !done && !active && "border-line text-secondary",
              )}
              aria-hidden="true"
            >
              {done ? (
                <Check className="h-3 w-3" />
              ) : active ? (
                <Loader2 className="h-3 w-3 animate-spin text-accent" />
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-line" />
              )}
            </span>
            <div className="flex items-baseline justify-between gap-3">
              <p
                className={cx(
                  "text-[13px]",
                  done || active ? "font-medium text-ink" : "text-secondary",
                )}
              >
                {step.label}
              </p>
              <p className="hidden text-xs text-secondary sm:block">
                {done ? "Done" : active ? step.detail + "…" : "Waiting"}
              </p>
            </div>
            <span className="sr-only">
              {done ? "done" : active ? "in progress" : "waiting"}
            </span>
          </li>
        );
      })}
      {failed ? (
        <li className="pt-1 text-xs text-secondary">
          Processing stopped — see the message below.
        </li>
      ) : null}
    </ol>
  );
}
