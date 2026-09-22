import type { PaperFigure, PaperTable } from "../../lib/types";

export function FiguresTablesViewer({
  figures,
  tables,
}: {
  figures: PaperFigure[];
  tables: PaperTable[];
}) {
  return (
    <div>
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        Detected structure · no image interpretation yet
      </p>
      <h2 className="mt-1 font-serif text-[22px] font-medium tracking-tight">
        Figures &amp; Tables
      </h2>

      {figures.length > 0 ? (
        <section aria-label="Figures" className="mt-6">
          <h3 className="text-[13px] font-semibold">
            Figures{" "}
            <span className="font-normal text-secondary">({figures.length})</span>
          </h3>
          <ul className="mt-3 flex max-w-3xl flex-col gap-2.5">
            {figures.map((fig, i) => (
              <li
                key={`f${i}`}
                className="rounded-[4px] border border-line bg-paper px-4 py-3"
              >
                <p className="text-sm font-medium">
                  {fig.number ? `Figure ${fig.number}` : "Figure"}
                  <span className="ml-2 font-normal text-secondary">
                    Page {fig.page}
                  </span>
                </p>
                {fig.caption ? (
                  <p className="mt-1 text-[13px] leading-relaxed text-secondary">
                    {fig.caption}
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-secondary italic">
                    No caption detected.
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {tables.length > 0 ? (
        <section aria-label="Tables" className="mt-6">
          <h3 className="text-[13px] font-semibold">
            Tables{" "}
            <span className="font-normal text-secondary">({tables.length})</span>
          </h3>
          <ul className="mt-3 flex max-w-3xl flex-col gap-2.5">
            {tables.map((table, i) => (
              <li
                key={`t${i}`}
                className="rounded-[4px] border border-line bg-paper px-4 py-3"
              >
                <p className="text-sm font-medium">
                  {table.number ? `Table ${table.number}` : "Table"}
                  <span className="ml-2 font-normal text-secondary">
                    Page {table.page}
                    {table.rows != null && table.cols != null
                      ? ` · ${table.rows}×${table.cols}`
                      : ""}
                  </span>
                </p>
                {table.caption ? (
                  <p className="mt-1 text-[13px] leading-relaxed text-secondary">
                    {table.caption}
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-secondary italic">
                    No caption detected.
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
