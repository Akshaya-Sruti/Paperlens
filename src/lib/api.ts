/**
 * Isolated backend communication layer (Stage 2).
 * All components must use these functions — no scattered fetch() calls.
 */

import type { AnalysisRecord, Paper, UploadResult } from "./types";

const API_BASE =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json();
    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof (data as { detail: unknown }).detail === "string"
    ) {
      return (data as { detail: string }).detail;
    }
  } catch {
    // fall through to generic message
  }
  return "Something went wrong. Please try again.";
}

function defaultMessage(status: number): string {
  if (status === 413) return "File exceeds the 20 MB limit.";
  if (status >= 500) return "The server had trouble reading this PDF.";
  return "Unable to process this PDF.";
}

export async function uploadPaper(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file, file.name);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/papers/upload`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the PaperLens server. Is the backend running?",
    );
  }

  if (!res.ok) {
    const detail = await readErrorMessage(res);
    throw new ApiError(
      res.status,
      detail === "Something went wrong. Please try again."
        ? defaultMessage(res.status)
        : detail,
    );
  }
  return (await res.json()) as UploadResult;
}

export async function getPaper(paperId: string): Promise<Paper> {
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/api/papers/${encodeURIComponent(paperId)}`,
    );
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the PaperLens server. Is the backend running?",
    );
  }
  if (!res.ok) {
    const detail = await readErrorMessage(res);
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as Paper;
}

export function apiBase(): string {
  return API_BASE;
}

/** Request AI analysis. Only call on explicit user action (or regenerate). */
export async function analyzePaper(
  paperId: string,
  force = false,
): Promise<AnalysisRecord> {
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/analyze`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force }),
      },
    );
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the PaperLens server. Is the backend running?",
    );
  }
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorMessage(res));
  }
  return (await res.json()) as AnalysisRecord;
}

/** Fetch a previously generated analysis (no AI call). */
export async function getPaperAnalysis(
  paperId: string,
): Promise<AnalysisRecord> {
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/analysis`,
    );
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the PaperLens server. Is the backend running?",
    );
  }
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorMessage(res));
  }
  return (await res.json()) as AnalysisRecord;
}

/** Rendered PNG for a detected figure/table region (may 404). */
export function mediaImageUrl(
  paperId: string,
  kind: "figure" | "table",
  index: number,
): string {
  return `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/media/${kind}/${index}/image`;
}
