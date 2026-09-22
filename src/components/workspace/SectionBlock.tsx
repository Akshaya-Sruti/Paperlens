import { Fragment, useMemo } from "react";
import type { PaperCitation, PaperSection } from "../../lib/types";
import { cx } from "../../lib/utils";

export function pageRangeLabel(start: number, end: number): string {
  return start === end ? `Page ${start}` : `Pages ${start}–${end}`;
}

export function SectionBlock({
  section,
  citations,
  highlightTerm,
  onCitationClick,
}: {
  section: PaperSection;
  citations: PaperCitation[];
  highlightTerm: string | null;
  onCitationClick: (referenceIndex: number) => void;
}) {
  const paragraphs = useMemo(
    () =>
      section.content
        .split(/\n\s*\n/)
        .map((p) => p.trim())
        .filter(Boolean),
    [section.content],
  );

  const HeadingTag = section.level >= 3 ? "h4" : section.level === 2 ? "h3" : "h2";

  return (
    <section
      id={`sec-${section.id}`}
      data-section-id={section.id}
      aria-label={section.title}
      className="scroll-mt-20"
    >
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        {section.number ? (
          <span className="mr-2 font-mono normal-case">§{section.number}</span>
        ) : null}
        {pageRangeLabel(section.start_page, section.end_page)}
      </p>
      <HeadingTag
        className={cx(
          "mt-1 font-serif font-medium tracking-tight",
          section.level <= 1 && "text-[22px]",
          section.level === 2 && "text-xl",
          section.level >= 3 && "text-lg",
        )}
      >
        {section.title}
      </HeadingTag>
      <div
        className={cx(
          "mt-4 max-w-2xl",
          section.level > 1 && "border-l-2 border-line pl-4",
        )}
      >
        {paragraphs.length > 0 ? (
          paragraphs.map((para, i) => (
            <ParagraphWithCitations
              key={i}
              paragraph={para}
              sectionStart={section.content.indexOf(para)}
              citations={citations}
              highlightTerm={highlightTerm}
              onCitationClick={onCitationClick}
            />
          ))
        ) : (
          <p className="text-sm text-secondary">
            No extractable text was found for this section.
          </p>
        )}
      </div>
      <details className="mt-4 max-w-2xl rounded-[4px] border border-line bg-paper px-3 py-2">
        <summary className="cursor-pointer text-[13px] font-medium text-secondary transition-colors hover:text-ink">
          View source
        </summary>
        <dl className="mt-2 flex flex-col gap-1 border-t border-line pt-2 font-mono text-xs text-secondary">
          <div className="flex gap-2">
            <dt className="w-16 shrink-0">Pages</dt>
            <dd>
              {section.start_page}
              {section.end_page !== section.start_page
                ? `–${section.end_page}`
                : ""}
            </dd>
          </div>
          <div className="flex gap-2">
            <dt className="w-16 shrink-0">Section</dt>
            <dd className="break-all">{section.id}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="w-16 shrink-0">Chars</dt>
            <dd>{section.content.length.toLocaleString()}</dd>
          </div>
        </dl>
        <p className="mt-2 max-h-40 overflow-y-auto border-t border-line pt-2 font-mono text-xs leading-relaxed whitespace-pre-wrap text-secondary">
          {section.content.slice(0, 1200)}
          {section.content.length > 1200 ? "…" : ""}
        </p>
      </details>
    </section>
  );
}

function ParagraphWithCitations({
  paragraph,
  sectionStart,
  citations,
  highlightTerm,
  onCitationClick,
}: {
  paragraph: string;
  sectionStart: number;
  citations: PaperCitation[];
  highlightTerm: string | null;
  onCitationClick: (referenceIndex: number) => void;
}) {
  const segments = useMemo(() => {
    type Seg =
      | { kind: "text"; text: string; key: string }
      | { kind: "cite"; cit: PaperCitation; key: string }
      | { kind: "mark"; text: string; key: string };

    const end = sectionStart + paragraph.length;
    const hits = citations
      .filter((c) => c.position >= sectionStart && c.position < end)
      .map((c) => ({ ...c, local: c.position - sectionStart }))
      .filter((c) => paragraph.slice(c.local, c.local + c.text.length) === c.text)
      .sort((a, b) => a.local - b.local);

    // Citation spans take precedence; search terms fill the gaps.
    const spans: Array<{ start: number; end: number; cit: (typeof hits)[number] }> = [];
    for (const hit of hits) {
      const s = hit.local;
      const e = s + hit.text.length;
      if (spans.some((o) => s < o.end && e > o.start)) continue;
      spans.push({ start: s, end: e, cit: hit });
    }
    spans.sort((a, b) => a.start - b.start);

    const out: Seg[] = [];
    let cursor = 0;
    let n = 0;
    const pushText = (from: number, to: number) => {
      if (from >= to) return;
      const slice = paragraph.slice(from, to);
      if (!highlightTerm) {
        out.push({ kind: "text", text: slice, key: `t${n++}` });
        return;
      }
      const lower = slice.toLowerCase();
      const term = highlightTerm.toLowerCase();
      let i = 0;
      let k = 0;
      for (;;) {
        const found = lower.indexOf(term, i);
        if (found === -1) break;
        if (found > i) {
          out.push({ kind: "text", text: slice.slice(i, found), key: `t${n++}` });
        }
        out.push({
          kind: "mark",
          text: slice.slice(found, found + term.length),
          key: `m${k++}`,
        });
        i = found + term.length;
      }
      if (i < slice.length) {
        out.push({ kind: "text", text: slice.slice(i), key: `t${n++}` });
      }
    };

    for (const span of spans) {
      pushText(cursor, span.start);
      out.push({ kind: "cite", cit: span.cit, key: `c${n++}` });
      cursor = span.end;
    }
    pushText(cursor, paragraph.length);
    return out;
  }, [citations, paragraph, sectionStart, highlightTerm]);

  return (
    <p className="mt-3 font-serif text-[15.5px] leading-[1.75] first:mt-0">
      {segments.map((seg) => {
        if (seg.kind === "text") {
          return <Fragment key={seg.key}>{seg.text}</Fragment>;
        }
        if (seg.kind === "mark") {
          return (
            <mark
              key={seg.key}
              className="rounded-[2px] bg-accent-soft px-0.5 text-inherit"
            >
              {seg.text}
            </mark>
          );
        }
        const linked = seg.cit.reference_index != null;
        return linked ? (
          <button
            key={seg.key}
            type="button"
            onClick={() =>
              onCitationClick(seg.cit.reference_index as number)
            }
            title={`Go to reference ${seg.cit.reference_index}`}
            aria-label={`Citation ${seg.cit.text}, go to reference ${seg.cit.reference_index}`}
            className="cursor-pointer rounded-[3px] bg-accent-soft px-0.5 font-sans text-[0.85em] font-medium text-accent transition-colors hover:bg-accent hover:text-white"
          >
            {seg.cit.text}
          </button>
        ) : (
          <span key={seg.key} title="No matching reference detected">
            {seg.cit.text}
          </span>
        );
      })}
    </p>
  );
}
