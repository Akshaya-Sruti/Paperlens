/** Shared TypeScript interfaces mirroring the Stage 3 API responses. */

export interface PageBlock {
  text: string;
  bbox: number[];
  font_size: number;
  bold: boolean;
}

export interface PaperPage {
  page_number: number;
  text: string;
  width: number;
  height: number;
  blocks: PageBlock[];
}

export interface PaperFigure {
  page: number;
  bbox: number[] | null;
  number: string | null;
  caption: string | null;
}

export interface PaperTable {
  page: number;
  bbox: number[] | null;
  rows: number | null;
  cols: number | null;
  number: string | null;
  caption: string | null;
}

export interface PaperEquation {
  page: number;
  text: string;
  bbox: number[] | null;
}

export interface PaperSection {
  id: string;
  title: string;
  original_title: string;
  normalized_type: string;
  number: string | null;
  level: number;
  parent_id: string | null;
  children: string[];
  start_page: number;
  end_page: number;
  content: string;
}

export interface PaperReference {
  raw_text: string;
  index: number | null;
  authors: string[];
  title: string | null;
  year: number | null;
  doi: string | null;
}

export interface PaperCitation {
  text: string;
  style: string;
  page: number;
  section_id: string | null;
  position: number;
  reference_index: number | null;
  reference_indices: number[];
}

export interface PaperAuthor {
  name: string;
  affiliation: string | null;
  email: string | null;
}

export interface PaperPublication {
  venue: string | null;
  volume: string | null;
  issue: string | null;
  page_range: string | null;
}

export interface ConceptCandidate {
  term: string;
  frequency: number;
  pages: number[];
}

export interface DocumentQuality {
  has_extractable_text: boolean;
  page_count: number;
  text_coverage: number;
  has_sections: boolean;
  has_references: boolean;
  has_abstract: boolean;
  is_probably_scanned: boolean;
  two_column: boolean;
  avg_chars_per_page: number;
}

export interface PaperMetadata {
  title_raw: string | null;
  author_raw: string | null;
  subject: string | null;
  keywords: string | null;
  creator: string | null;
  producer: string | null;
  creation_date: string | null;
  modification_date: string | null;
}

export type PaperStatus = "processed" | "scanned";

export interface Paper {
  id: string;
  filename: string;
  title: string | null;
  authors: PaperAuthor[];
  affiliations: string[];
  raw_author_text: string | null;
  year: number | null;
  publication: PaperPublication;
  doi: string | null;
  urls: string[];
  abstract: string | null;
  keywords: string[];
  page_count: number;
  pages: PaperPage[];
  sections: PaperSection[];
  references: PaperReference[];
  citations: PaperCitation[];
  figures: PaperFigure[];
  tables: PaperTable[];
  equations: PaperEquation[];
  concept_candidates: ConceptCandidate[];
  quality: DocumentQuality;
  metadata: PaperMetadata;
  has_selectable_text: boolean;
  status: PaperStatus;
}

export interface UploadResult {
  paper_id: string;
  filename: string;
  status: PaperStatus;
}
