import {
  ArrowRight,
  GitCompareArrows,
  Layers,
  Lightbulb,
  MessagesSquare,
  ScanSearch,
  SlidersHorizontal,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Footer } from "../components/layout/Footer";
import { Navbar } from "../components/layout/Navbar";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody } from "../components/ui/Card";
import { useDocumentTitle } from "../lib/useDocumentTitle";

const OUTLINE = [
  { section: "Abstract", lines: 2, indent: 0 },
  { section: "Introduction", lines: 3, indent: 0 },
  { section: "Methodology", lines: 3, indent: 0 },
  { section: "Results", lines: 2, indent: 0 },
  { section: "Conclusion", lines: 2, indent: 0 },
];

function PaperOutlineVisual() {
  return (
    <div
      className="overflow-hidden rounded-[4px] border border-line bg-surface shadow-[0_1px_2px_rgba(23,23,23,0.05)]"
      role="img"
      aria-label="Illustration of a research paper organized into abstract, introduction, methodology, results, and conclusion"
    >
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <span className="flex items-center gap-2 text-xs font-medium text-secondary">
          <span className="inline-block h-2 w-2 rounded-[2px] bg-accent" aria-hidden="true" />
          paper.pdf — organized
        </span>
        <span className="text-[11px] text-secondary">5 sections</span>
      </div>
      <ol className="divide-y divide-line">
        {OUTLINE.map((block, i) => (
          <li key={block.section} className="flex gap-3 px-4 py-3">
            <span className="w-6 shrink-0 font-mono text-[11px] text-secondary">
              {String(i + 1).padStart(2, "0")}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold tracking-[0.08em] uppercase">
                {block.section}
              </p>
              <div className="mt-2 flex flex-col gap-1.5" aria-hidden="true">
                {Array.from({ length: block.lines }).map((_, j) => (
                  <span
                    key={j}
                    className="block h-1.5 rounded-[2px] bg-muted"
                    style={{ width: `${92 - j * 14 - (i % 2) * 6}%` }}
                  />
                ))}
              </div>
            </div>
            <span
              className="mt-0.5 h-4 w-1 shrink-0 rounded-[2px] bg-accent/70"
              aria-hidden="true"
              style={{ opacity: 1 - i * 0.14 }}
            />
          </li>
        ))}
      </ol>
      <div className="border-t border-line bg-paper px-4 py-2.5">
        <p className="text-[11px] text-secondary">
          Explanation level: <span className="font-medium text-ink">Intermediate</span>
        </p>
      </div>
    </div>
  );
}

const STEPS = [
  {
    n: "01",
    title: "Upload",
    text: "Add your research paper.",
  },
  {
    n: "02",
    title: "Understand",
    text: "PaperLens organizes the paper into meaningful sections.",
  },
  {
    n: "03",
    title: "Explore",
    text: "Read explanations at the difficulty level that works for you.",
  },
];

const FEATURES = [
  {
    icon: Layers,
    title: "Structured paper understanding",
    text: "Papers broken into overview, method, results, and limitations — so you always know where you are.",
    status: "Foundation" as const,
  },
  {
    icon: SlidersHorizontal,
    title: "Difficulty-adaptive explanations",
    text: "Move from plain-language overviews to full research depth without losing the thread.",
    status: "Foundation" as const,
  },
  {
    icon: Lightbulb,
    title: "Concept explanations",
    text: "Unfamiliar terms and methods explained in the context of the paper you are reading.",
    status: "Planned" as const,
  },
  {
    icon: MessagesSquare,
    title: "Paper-based Q&A",
    text: "Ask questions grounded in the paper itself, with answers that point back to the source.",
    status: "Later" as const,
  },
  {
    icon: ScanSearch,
    title: "Research gap analysis",
    text: "See what the paper leaves open — limitations, assumptions, and directions for future work.",
    status: "Later" as const,
  },
  {
    icon: GitCompareArrows,
    title: "Literature comparison",
    text: "Place a paper alongside related work to compare methods, datasets, and findings.",
    status: "Later" as const,
  },
];

export function Home() {
  useDocumentTitle("PaperLens — Understand research. Your way.");
  return (
    <div className="page-enter min-h-screen">
      <Navbar />
      <main>
        {/* Hero */}
        <section className="border-b border-line">
          <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-2 md:items-center md:py-20">
            <div>
              <p className="inline-flex items-center gap-2 border border-line bg-surface px-2.5 py-1 text-[11px] font-medium tracking-wide text-secondary uppercase">
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full bg-accent"
                  aria-hidden="true"
                />
                For students reading research
              </p>
              <h1 className="mt-5 font-serif text-4xl leading-[1.12] font-medium tracking-tight md:text-[44px]">
                Understand research papers.
              </h1>
              <p className="mt-4 max-w-md text-[15.5px] leading-relaxed text-secondary">
                Turn dense research papers into structured, understandable
                insights — at your level.
              </p>
              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Link to="/upload">
                  <Button>
                    Upload a paper
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </Link>
                <a href="#how-it-works">
                  <Button variant="secondary">See how it works</Button>
                </a>
              </div>
              <p className="mt-5 text-[13px] text-secondary">
                PDF only · up to 20 MB · no account needed for Stage 1
              </p>
            </div>
            <PaperOutlineVisual />
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="scroll-mt-16 border-b border-line">
          <div className="mx-auto max-w-6xl px-5 py-14 md:py-16">
            <p className="text-[11px] font-medium tracking-[0.1em] text-secondary uppercase">
              How it works
            </p>
            <h2 className="mt-2 font-serif text-2xl font-medium tracking-tight md:text-[28px]">
              Three steps, no clutter.
            </h2>
            <ol className="mt-8 grid gap-px overflow-hidden rounded-[4px] border border-line bg-line md:grid-cols-3">
              {STEPS.map((s) => (
                <li key={s.n} className="bg-surface px-6 py-6">
                  <p className="font-mono text-xs text-accent">{s.n}</p>
                  <h3 className="mt-2 text-[15px] font-semibold">{s.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-secondary">
                    {s.text}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="scroll-mt-16">
          <div className="mx-auto max-w-6xl px-5 py-14 md:py-16">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium tracking-[0.1em] text-secondary uppercase">
                  Capabilities
                </p>
                <h2 className="mt-2 font-serif text-2xl font-medium tracking-tight md:text-[28px]">
                  Built for how students actually read.
                </h2>
              </div>
              <p className="max-w-sm text-[13px] leading-relaxed text-secondary">
                Stage 1 establishes the foundation. Advanced capabilities are
                marked honestly below.
              </p>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((f) => (
                <Card key={f.title}>
                  <CardBody>
                    <div className="flex items-start justify-between gap-3">
                      <span className="flex h-8 w-8 items-center justify-center rounded-[4px] border border-line bg-muted text-ink">
                        <f.icon className="h-4 w-4" aria-hidden="true" />
                      </span>
                      {f.status === "Foundation" ? (
                        <Badge tone="accent">Stage 1</Badge>
                      ) : (
                        <Badge>Coming later</Badge>
                      )}
                    </div>
                    <h3 className="mt-4 text-[14.5px] font-semibold">
                      {f.title}
                    </h3>
                    <p className="mt-1.5 text-[13.5px] leading-relaxed text-secondary">
                      {f.text}
                    </p>
                  </CardBody>
                </Card>
              ))}
            </div>

            <div className="mt-8 flex flex-col items-start justify-between gap-4 border-t border-line pt-6 sm:flex-row sm:items-center">
              <p className="text-sm text-secondary">
                Have a paper in mind? Start with the upload flow.
              </p>
              <Link to="/upload">
                <Button variant="secondary">
                  Upload a paper
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
