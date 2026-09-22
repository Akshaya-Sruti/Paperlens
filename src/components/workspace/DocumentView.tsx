import { Fragment, useState } from "react";
import type { Paper, PaperFigure, PaperTable } from "../../lib/types";
import { mediaImageUrl } from "../../lib/api";
import { cx } from "../../lib/utils";
import { PaperHeader } from "./PaperHeader";
import { ReferencesViewer } from "./ReferencesViewer";
import { ScannedNotice } from "./ScannedNotice";
import { SectionBlock, pageRangeLabel } from "./SectionBlock";

export function DocumentView({
  paper,
  highlightTerm,
  highlightAnchor,
  refHighlight,
  onCitationClick,
}: {
  paper: Paper;
  highlightTerm: string | null;
  highlightAnchor: string | null;
  refHighlight: number | null;
  onCitationClick: (referenceIndex: number) => void;
}) {
  const citationsBySection = new Map<string, typeof paper.citations>();
  for (const cit of paper.citations) {
    if (!cit.section_id) continue;
    const list = citationsBySection.get(cit.section_id) ?? [];
    list.push(cit);
    citationsBySection.set(cit.section_id, list);
  }

  const topLevel = paper.sections.filter((s) => s.level === 1);
  const abstractSection = paper.sections.find(
    (s) => s.normalized_type === "abstract",
  );
  const bodySections = paper.sections.filter(
    (s) => s.normalized_type !== "abstract",
  );
  const hasFigures = paper.figures.length > 0 || paper.tables.length > 0;

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div id="top" data-spy="overview" className="scroll-mt-20">
        <PaperHeader paper={paper} />
      </div>

      {paper.status === "scanned" ? (
        <div className="mt-6">
          <ScannedNotice />
        </div>
      ) : null}

      <section
        id="abstract"
        data-spy={abstractSection ? `section:${abstractSection.id}` : "overview"}
        aria-label="Abstract"
        className="mt-8 scroll-mt-20"
      >
        <h2 className="font-serif text-[22px] font-medium tracking-tight">
          Abstract
        </h2>
        {paper.abstract ? (
          <>
            <p className="mt-1 text-xs text-secondary">Page 1</p>
            <div className="mt-3">
              {paper.abstract.split(/\n\s*\n/).map((para, i) => (
                <p
                  key={i}
                  className="mt-3 font-serif text-[15.5px] leading-[1.75] first:mt-0"
                >
                  <MarkedText
                    text={para}
                    term={
                      highlightAnchor === "abstract" ? highlightTerm : null
                    }
                  />
                </p>
              ))}
            </div>
          </>
        ) : (
          <p className="mt-2 text-sm text-secondary">
            No abstract was detected in this paper.
          </p>
        )}

        <div className="mt-6">
          <h3 className="text-[11px] font-medium tracking-wide text-secondary uppercase">
            Keywords
          </h3>
          {paper.keywords.length > 0 ? (
            <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Keywords">
              {paper.keywords.map((kw) => (
                <li
                  key={kw}
                  className="rounded-[3px] border border-line bg-surface px-2 py-1 text-[13px]"
                >
                  {kw}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-secondary">
              No explicit keywords were found in this paper.
            </p>
          )}
        </div>
      </section>

      {topLevel.length > 0 ? (
        <section aria-label="Paper structure" className="mt-8 border-t border-line pt-6">
          <h2 className="text-[11px] font-medium tracking-wide text-secondary uppercase">
            Paper structure
          </h2>
          <ol className="mt-3 flex flex-col">
            {topLevel.slice(0, 14).map((section, i) => (
              <li key={section.id} className="flex flex-col">
                <a
                  href={`#sec-${section.id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById(`sec-${section.id}`)
                      ?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                  className="flex items-baseline gap-3 rounded-[4px] py-1 transition-colors hover:bg-muted"
                >
                  <span className="w-8 shrink-0 font-mono text-[11px] text-secondary">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="text-sm">
                    {section.number ? (
                      <span className="mr-2 font-mono text-xs text-secondary">
                        {section.number}
                      </span>
                    ) : null}
                    {section.title}
                  </span>
                  <span className="ml-auto shrink-0 text-xs text-secondary">
                    {pageRangeLabel(section.start_page, section.end_page)}
                  </span>
                </a>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <div className="mt-8 border-t border-line pt-6">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm sm:grid-cols-3">
          <DocDetail label="Pages" value={String(paper.page_count)} />
          <DocDetail label="Sections" value={String(paper.sections.length)} />
          <DocDetail
            label="References"
            value={String(paper.references.length)}
          />
          <DocDetail
            label="Coverage"
            value={`${Math.round(paper.quality.text_coverage * 100)}% of pages`}
          />
          <DocDetail
            label="Layout"
            value={paper.quality.two_column ? "Two-column" : "Single-column"}
          />
          <DocDetail label="Source" value={paper.filename} truncate />
        </dl>
      </div>

      {bodySections.length > 0 ? (
        <div className="mt-10 flex flex-col gap-10 border-t border-line pt-8">
          {bodySections.map((section) => (
            <div
              key={section.id}
              data-spy={`section:${section.id}`}
              className="scroll-mt-20"
            >
              <SectionBlock
                section={section}
                citations={citationsBySection.get(section.id) ?? []}
                highlightTerm={
                  highlightAnchor === `sec-${section.id}` ? highlightTerm : null
                }
                onCitationClick={onCitationClick}
              />
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-10 border-t border-line pt-6 text-sm text-secondary">
          No sections were detected in this paper. You can still inspect the
          raw extracted text.
        </p>
      )}

      {hasFigures ? (
        <section
          id="figures"
          data-spy="figures"
          aria-label="Figures and tables"
          className="mt-10 scroll-mt-20 border-t border-line pt-8"
        >
          <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
            Detected structure
          </p>
          <h2 className="mt-1 font-serif text-[22px] font-medium tracking-tight">
            Figures &amp; Tables
          </h2>
          {paper.figures.length > 0 ? (
            <div className="mt-5">
              <h3 className="text-[13px] font-semibold">
                Figures{" "}
                <span className="font-normal text-secondary">
                  ({paper.figures.length})
                </span>
              </h3>
              <div className="mt-3 flex flex-col gap-3">
                {paper.figures.map((fig, i) => (
                  <FigureCard
                    key={`f${i}`}
                    paperId={paper.id}
                    kind="figure"
                    index={i}
                    item={fig}
                  />
                ))}
              </div>
            </div>
          ) : null}
          {paper.tables.length > 0 ? (
            <div className="mt-6">
              <h3 className="text-[13px] font-semibold">
                Tables{" "}
                <span className="font-normal text-secondary">
                  ({paper.tables.length})
                </span>
              </h3>
              <div className="mt-3 flex flex-col gap-3">
                {paper.tables.map((table, i) => (
                  <FigureCard
                    key={`t${i}`}
                    paperId={paper.id}
                    kind="table"
                    index={i}
                    item={table}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {paper.references.length > 0 ? (
        <div
          id="references"
          data-spy="references"
          className="mt-10 scroll-mt-20 border-t border-line pt-8"
        >
          <ReferencesViewer
            references={paper.references}
            highlightIndex={refHighlight}
          />
        </div>
      ) : (
        <p className="mt-10 border-t border-line pt-6 text-sm text-secondary">
          No references were detected in this paper.
        </p>
      )}
    </div>
  );
}

function MarkedText({ text, term }: { text: string; term: string | null }) {
  if (!term) return <>{text}</>;
  const lower = text.toLowerCase();
  const needle = term.toLowerCase();
  const parts: React.ReactNode[] = [];
  let i = 0;
  let k = 0;
  for (;;) {
    const found = lower.indexOf(needle, i);
    if (found === -1) break;
    if (found > i) parts.push(<Fragment key={`t${k}`}>{text.slice(i, found)}</Fragment>);
    parts.push(
      <mark
        key={`m${k}`}
        className="rounded-[2px] bg-accent-soft px-0.5 text-inherit"
      >
        {text.slice(found, found + needle.length)}
      </mark>,
    );
    k += 1;
    i = found + needle.length;
  }
  if (i < text.length) parts.push(<Fragment key={`t${k}`}>{text.slice(i)}</Fragment>);
  return <>{parts}</>;
}

function DocDetail({
  label,
  value,
  truncate = false,
}: {
  label: string;
  value: string;
  truncate?: boolean;
}) {
  return (
    <div className="flex gap-2">
      <dt className="shrink-0 text-secondary">{label}</dt>
      <dd className={cx(truncate && "truncate")} title={value}>
        {value}
      </dd>
    </div>
  );
}

function FigureCard({
  paperId,
  kind,
  index,
  item,
}: {
  paperId: string;
  kind: "figure" | "table";
  index: number;
  item: PaperFigure | PaperTable;
}) {
  const [failed, setFailed] = useState(false);
  const name =
    kind === "figure"
      ? item.number
        ? `Figure ${item.number}`
        : "Figure"
      : item.number
        ? `Table ${item.number}`
        : "Table";

  return (
    <figure className="rounded-[4px] border border-line bg-surface px-4 py-3">
      <figcaption className="text-sm font-medium">
        {name}
        <span className="ml-2 font-normal text-secondary">
          Page {item.page}
        </span>
      </figcaption>
      {!failed ? (
        <img
          src={mediaImageUrl(paperId, kind, index)}
          alt={`${name} region rendered from page ${item.page}`}
          loading="lazy"
          onError={() => setFailed(true)}
          className="mt-3 max-h-96 w-auto rounded-[3px] border border-line"
        />
      ) : (
        <p className="mt-2 text-xs text-secondary italic">
          {name} detected on page {item.page} — image preview unavailable.
        </p>
      )}
      {item.caption ? (
        <p className="mt-2 text-[13px] leading-relaxed text-secondary">
          {item.caption}
        </p>
      ) : (
        <p className="mt-2 text-xs text-secondary italic">
          No caption detected.
        </p>
      )}
    </figure>
  );
}
