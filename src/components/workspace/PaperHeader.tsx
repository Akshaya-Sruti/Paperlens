import type { Paper } from "../../lib/types";

export function PaperHeader({ paper }: { paper: Paper }) {
  const names = paper.authors.map((a) => a.name);
  return (
    <div>
      <nav aria-label="Breadcrumb">
        <p className="text-xs text-secondary">
          <span>Papers</span>
          <span aria-hidden="true" className="mx-1.5">
            /
          </span>
          <span className="text-ink">{paper.title ?? paper.filename}</span>
        </p>
      </nav>
      <p className="mt-5 text-[11px] font-medium tracking-[0.12em] text-secondary uppercase">
        Research paper
      </p>
      <h1 className="mt-2 max-w-2xl font-serif text-3xl leading-[1.2] font-medium tracking-tight md:text-4xl">
        {paper.title ?? paper.filename}
      </h1>
      {!paper.title ? (
        <p className="mt-2 text-xs text-secondary">
          Title not detected — showing filename.
        </p>
      ) : null}
      {names.length > 0 ? (
        <p className="mt-3 max-w-2xl text-[14.5px] leading-relaxed">
          <span className="text-secondary">Authors: </span>
          {names.join(" · ")}
        </p>
      ) : null}
      <p className="mt-1.5 text-sm text-secondary">
        {[paper.publication.venue, paper.year ? String(paper.year) : null]
          .filter(Boolean)
          .join(" · ") || "Publication details not detected"}
      </p>
      {paper.doi ? (
        <p className="mt-1.5 text-sm">
          <span className="text-secondary">DOI: </span>
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noreferrer"
            className="font-medium text-accent underline underline-offset-2"
          >
            {paper.doi}
          </a>
        </p>
      ) : null}
    </div>
  );
}
