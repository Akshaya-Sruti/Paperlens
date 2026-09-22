import { Loader2, RotateCcw } from "lucide-react";
import type {
  AnalysisEvidence,
  AnalysisKeyFinding,
  AnalysisListBlock,
  AnalysisRichBlock,
  Paper,
  PaperAnalysis,
} from "../../lib/types";
import { Button } from "../ui/Button";

export type AnalysisUiState = "idle" | "loading" | "ready" | "error";

export function AnalysisSection({
  paper,
  analysis,
  uiState,
  error,
  onAnalyze,
  onEvidenceClick,
}: {
  paper: Paper;
  analysis: PaperAnalysis | null;
  uiState: AnalysisUiState;
  error: string | null;
  onAnalyze: (force: boolean) => void;
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
}) {
  return (
    <section
      id="analysis"
      data-spy="analysis"
      aria-label="AI analysis"
      className="mt-10 scroll-mt-20 border-t border-line pt-8"
    >
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        AI analysis
      </p>
      <h2 className="mt-1 font-serif text-[22px] font-medium tracking-tight">
        Paper analysis
      </h2>

      {uiState === "idle" ? (
        <div className="mt-4 max-w-2xl rounded-[4px] border border-line bg-paper px-5 py-6">
          <h3 className="font-serif text-lg font-medium tracking-tight">
            Understand this paper
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-secondary">
            Generate a structured analysis of this paper using its extracted
            content — problem, methods, results, and findings, each linked to
            its source.
          </p>
          {paper.has_selectable_text ? (
            <Button onClick={() => onAnalyze(false)} className="mt-4">
              Analyze paper
            </Button>
          ) : (
            <p className="mt-4 text-sm text-secondary">
              Analysis needs extractable text, which this scanned paper does
              not have yet.
            </p>
          )}
        </div>
      ) : null}

      {uiState === "loading" ? (
        <div
          className="mt-4 flex max-w-2xl items-start gap-3 rounded-[4px] border border-line bg-paper px-5 py-5"
          role="status"
          aria-label="Analyzing paper"
        >
          <Loader2
            className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-accent"
            aria-hidden="true"
          />
          <div>
            <p className="text-sm font-medium">Analyzing paper…</p>
            <p className="mt-1 text-[13px] leading-relaxed text-secondary">
              Reading the extracted sections and structuring the findings.
              This usually takes under a minute — the rest of the workspace
              stays usable.
            </p>
          </div>
        </div>
      ) : null}

      {uiState === "error" ? (
        <div
          role="alert"
          className="mt-4 max-w-2xl rounded-[4px] border border-accent/30 bg-accent-soft px-5 py-5"
        >
          <p className="text-sm font-medium text-ink">
            Analysis could not be generated.
          </p>
          <p className="mt-1 text-[13px] text-secondary">{error}</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onAnalyze(false)}
            className="mt-3"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Try again
          </Button>
        </div>
      ) : null}

      {uiState === "ready" && analysis ? (
        <AnalysisBody
          analysis={analysis}
          onEvidenceClick={onEvidenceClick}
          onRegenerate={() => onAnalyze(true)}
        />
      ) : null}
    </section>
  );
}

function AnalysisBody({
  analysis,
  onEvidenceClick,
  onRegenerate,
}: {
  analysis: PaperAnalysis;
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
  onRegenerate: () => void;
}) {
  return (
    <div className="mt-2 max-w-2xl">
      <RichBlockView title="Summary" block={analysis.summary} onEvidenceClick={onEvidenceClick} />
      <RichBlockView title="Research problem" block={analysis.research_problem} onEvidenceClick={onEvidenceClick} />
      <ListBlockView title="Objectives" block={analysis.objectives} onEvidenceClick={onEvidenceClick} />
      <RichBlockView title="Methodology" block={analysis.methodology} onEvidenceClick={onEvidenceClick} />
      <RichBlockView title="Dataset" block={analysis.dataset} onEvidenceClick={onEvidenceClick} />
      <ListBlockView title="Models" block={analysis.models} onEvidenceClick={onEvidenceClick} />
      <RichBlockView title="Results" block={analysis.results} onEvidenceClick={onEvidenceClick} />
      <ListBlockView title="Limitations" block={analysis.limitations} onEvidenceClick={onEvidenceClick} />
      <ListBlockView title="Future work" block={analysis.future_work} onEvidenceClick={onEvidenceClick} />
      <ListBlockView title="Contributions" block={analysis.contributions} onEvidenceClick={onEvidenceClick} />

      {analysis.key_findings.length > 0 ? (
        <div className="mt-6">
          <h3 className="text-[15px] font-semibold">Key findings</h3>
          <ol className="mt-3 flex flex-col gap-4">
            {analysis.key_findings.map((finding, i) => (
              <KeyFindingView
                key={i}
                index={i + 1}
                finding={finding}
                onEvidenceClick={onEvidenceClick}
              />
            ))}
          </ol>
        </div>
      ) : null}

      <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
        <p className="text-xs text-secondary">
          Analyzed
          {analysis.meta.created_at
            ? ` ${new Date(analysis.meta.created_at).toLocaleDateString()}`
            : ""}
          {analysis.meta.model ? ` · ${analysis.meta.model}` : ""}
          {analysis.meta.truncated ? " · long paper, lower-priority sections trimmed" : ""}
        </p>
        <Button variant="secondary" size="sm" onClick={onRegenerate}>
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Regenerate analysis
        </Button>
      </div>
    </div>
  );
}

function RichBlockView({
  title,
  block,
  onEvidenceClick,
}: {
  title: string;
  block: AnalysisRichBlock;
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
}) {
  if (!block.text && !block.interpretation && block.evidence.length === 0) {
    return null;
  }
  return (
    <div className="mt-6">
      <h3 className="text-[15px] font-semibold">{title}</h3>
      {block.text ? (
        <p className="mt-2 font-serif text-[15.5px] leading-[1.75]">
          {block.text}
        </p>
      ) : null}
      {block.interpretation ? (
        <div className="mt-2 rounded-[4px] border-l-2 border-accent/50 bg-paper px-3 py-2">
          <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
            AI interpretation
          </p>
          <p className="mt-1 text-sm leading-relaxed">{block.interpretation}</p>
        </div>
      ) : null}
      <EvidenceSources evidence={block.evidence} onEvidenceClick={onEvidenceClick} />
    </div>
  );
}

function ListBlockView({
  title,
  block,
  onEvidenceClick,
}: {
  title: string;
  block: AnalysisListBlock;
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
}) {
  if (block.items.length === 0 && block.evidence.length === 0) {
    return null;
  }
  return (
    <div className="mt-6">
      <h3 className="text-[15px] font-semibold">{title}</h3>
      {block.items.length > 0 ? (
        <ul className="mt-2 flex flex-col gap-1.5">
          {block.items.map((item, i) => (
            <li
              key={i}
              className="flex gap-2.5 font-serif text-[15px] leading-relaxed"
            >
              <span aria-hidden="true" className="text-secondary">
                —
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-secondary">Not explicitly stated.</p>
      )}
      <EvidenceSources evidence={block.evidence} onEvidenceClick={onEvidenceClick} />
    </div>
  );
}

function KeyFindingView({
  index,
  finding,
  onEvidenceClick,
}: {
  index: number;
  finding: AnalysisKeyFinding;
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
}) {
  return (
    <li className="flex gap-3">
      <span className="shrink-0 font-mono text-xs text-secondary">
        {String(index).padStart(2, "0")}
      </span>
      <div className="min-w-0">
        <p className="font-serif text-[15px] leading-relaxed">
          {finding.statement}
        </p>
        {finding.interpretation ? (
          <div className="mt-2 rounded-[4px] border-l-2 border-accent/50 bg-paper px-3 py-2">
            <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
              AI interpretation
            </p>
            <p className="mt-1 text-sm leading-relaxed">
              {finding.interpretation}
            </p>
          </div>
        ) : null}
        <EvidenceSources evidence={finding.evidence} onEvidenceClick={onEvidenceClick} />
      </div>
    </li>
  );
}

function EvidenceSources({
  evidence,
  onEvidenceClick,
}: {
  evidence: AnalysisEvidence[];
  onEvidenceClick: (evidence: AnalysisEvidence) => void;
}) {
  if (evidence.length === 0) return null;
  return (
    <div className="mt-2.5">
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        Sources
      </p>
      <ul className="mt-1.5 flex flex-col gap-1.5">
        {evidence.map((ev, i) => (
          <li key={i} className="border-l border-line pl-2.5">
            <button
              type="button"
              onClick={() => onEvidenceClick(ev)}
              title={ev.section ? `Go to ${ev.section}` : "Source reference"}
              className="cursor-pointer text-xs font-medium text-accent underline-offset-2 hover:underline"
            >
              {ev.section ?? "Paper"}
              {ev.page != null ? ` · p. ${ev.page}` : ""}
            </button>
            {ev.text ? (
              <p className="mt-0.5 text-xs leading-relaxed text-secondary">
                “{ev.text.length > 220 ? ev.text.slice(0, 220) + "…" : ev.text}”
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
