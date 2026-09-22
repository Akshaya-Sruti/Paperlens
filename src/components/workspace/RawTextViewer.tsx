import { useState } from "react";
import type { PaperPage } from "../../lib/types";
import { Button } from "../ui/Button";

const PAGE_SIZE = 10;

/** Transparency view: exactly what was extracted, page by page. */
export function RawTextViewer({ pages }: { pages: PaperPage[] }) {
  const [visible, setVisible] = useState(PAGE_SIZE);
  const shown = pages.slice(0, visible);

  return (
    <div>
      <p className="text-[11px] font-medium tracking-wide text-secondary uppercase">
        Extracted text · {pages.length} {pages.length === 1 ? "page" : "pages"}
      </p>
      <h2 className="mt-1 font-serif text-[22px] font-medium tracking-tight">
        Extracted text
      </h2>
      <div className="mt-5 flex max-w-3xl flex-col gap-4">
        {shown.map((page) => (
          <section
            key={page.page_number}
            aria-label={`Extracted text, page ${page.page_number}`}
            className="rounded-[4px] border border-line"
          >
            <header className="border-b border-line bg-paper px-4 py-2">
              <p className="font-mono text-xs text-secondary">
                Page {page.page_number}
              </p>
            </header>
            <p className="px-4 py-3 text-[13.5px] leading-relaxed whitespace-pre-wrap">
              {page.text.trim() || (
                <span className="text-secondary italic">
                  No selectable text on this page.
                </span>
              )}
            </p>
          </section>
        ))}
      </div>
      {visible < pages.length ? (
        <div className="mt-5">
          <Button variant="secondary" onClick={() => setVisible((v) => v + PAGE_SIZE)}>
            Show more pages ({pages.length - visible} remaining)
          </Button>
        </div>
      ) : null}
    </div>
  );
}
