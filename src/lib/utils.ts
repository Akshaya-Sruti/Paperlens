export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function formatBytes(bytes: number, decimals = 1): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes === 0) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / Math.pow(1024, i);
  const formatted =
    value >= 100 ? Math.round(value).toString() : value.toFixed(decimals);
  return `${formatted} ${units[i]}`;
}

export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

export function validatePdfFile(file: File): string | null {
  const isPdf =
    file.type === "application/pdf" ||
    file.name.toLowerCase().endsWith(".pdf");
  if (!isPdf) return "Only PDF files are supported.";
  if (file.size > MAX_UPLOAD_BYTES)
    return "File exceeds the 20 MB limit. Please choose a smaller PDF.";
  if (file.size === 0) return "This file appears to be empty.";
  return null;
}
