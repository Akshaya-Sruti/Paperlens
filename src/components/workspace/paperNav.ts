import type { LucideIcon } from "lucide-react";
import {
  BookMarked,
  FileSearch,
  FileText,
  FlaskConical,
  Images,
  ListTree,
  ScanSearch,
  ScrollText,
  BarChart3,
  Flag,
} from "lucide-react";
import type { PaperSection } from "../../lib/types";

export interface NavEntry {
  id: string;
  label: string;
  icon: LucideIcon;
  /** Underlying section id, or a virtual view ("overview", "references"). */
  target: string;
  kind: "view" | "section" | "references" | "figures" | "raw";
  level: number;
}

export interface NavGroup {
  heading: string;
  entries: NavEntry[];
}

export interface PaperNav {
  groups: NavGroup[];
  referencesCount: number;
}

const BUCKETS: Array<{
  label: string;
  icon: LucideIcon;
  match: string[];
}> = [
  { label: "Abstract", icon: FileText, match: ["abstract"] },
  {
    label: "Introduction",
    icon: ScanSearch,
    match: ["introduction"],
  },
  {
    label: "Methodology",
    icon: FlaskConical,
    match: ["methodology", "dataset"],
  },
  {
    label: "Results",
    icon: BarChart3,
    match: ["results", "discussion", "experiments"],
  },
  {
    label: "Conclusion",
    icon: Flag,
    match: ["conclusion", "future_work", "limitations"],
  },
];

function withNumber(section: PaperSection, label: string): string {
  return section.number ? `${section.number}  ${label}` : label;
}

/** Map detected sections onto the stable workspace navigation. */
export function buildPaperNav(
  sections: PaperSection[],
  referencesCount: number,
  figuresCount: number,
): PaperNav {
  const claimed = new Set<string>();
  const contents: NavEntry[] = [];

  for (const bucket of BUCKETS) {
    const found = sections.find(
      (s) => !claimed.has(s.id) && bucket.match.includes(s.normalized_type),
    );
    if (found) {
      claimed.add(found.id);
      contents.push({
        id: `section:${found.id}`,
        label: withNumber(found, bucket.label),
        icon: bucket.icon,
        target: found.id,
        kind: "section",
        level: found.level,
      });
    }
  }

  for (const s of sections) {
    if (claimed.has(s.id)) continue;
    claimed.add(s.id);
    contents.push({
      id: `section:${s.id}`,
      label: withNumber(s, s.title),
      icon: ListTree,
      target: s.id,
      kind: "section",
      level: s.level,
    });
  }

  const additional: NavEntry[] = [];
  if (figuresCount > 0) {
    additional.push({
      id: "figures",
      label: "Figures & Tables",
      icon: Images,
      target: "figures",
      kind: "figures",
      level: 1,
    });
  }
  if (referencesCount > 0) {
    additional.push({
      id: "references",
      label: "References",
      icon: BookMarked,
      target: "references",
      kind: "references",
      level: 1,
    });
  }
  additional.push({
    id: "raw",
    label: "Extracted text",
    icon: FileText,
    target: "raw",
    kind: "raw",
    level: 1,
  });

  const groups: NavGroup[] = [
    {
      heading: "Paper",
      entries: [
        {
          id: "overview",
          label: "Overview",
          icon: ScrollText,
          target: "overview",
          kind: "view",
          level: 1,
        },
        {
          id: "analysis",
          label: "AI Analysis",
          icon: FileSearch,
          target: "analysis",
          kind: "view",
          level: 1,
        },
      ],
    },
  ];
  if (contents.length > 0) {
    groups.push({ heading: "Contents", entries: contents });
  }
  groups.push({ heading: "Additional", entries: additional });

  return { groups, referencesCount };
}
