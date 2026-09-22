import { FileUp } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { cx } from "../../lib/utils";

interface UploadDropzoneProps {
  onFileAccepted: (file: File) => void;
  onError: (message: string | null) => void;
  error: string | null;
  disabled?: boolean;
}

export function UploadDropzone({
  onFileAccepted,
  onError,
  error,
  disabled = false,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const dragCounter = useRef(0);

  const openPicker = useCallback(() => {
    if (disabled) return;
    inputRef.current?.click();
  }, [disabled]);

  const handleDragEnter = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;
      dragCounter.current += 1;
      setDragActive(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current = Math.max(0, dragCounter.current - 1);
    if (dragCounter.current === 0) setDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      setDragActive(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (!file) return;
      onError(null);
      onFileAccepted(file);
    },
    [disabled, onFileAccepted, onError],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      // Reset so the same file can be picked again after removal.
      e.target.value = "";
      if (!file) return;
      onError(null);
      onFileAccepted(file);
    },
    [onFileAccepted, onError],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openPicker();
      }
    },
    [openPicker],
  );

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload a PDF research paper. Activate to open the file picker."
        aria-disabled={disabled}
        onClick={openPicker}
        onKeyDown={handleKeyDown}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={cx(
          "flex cursor-pointer flex-col items-center justify-center rounded-[4px] border border-dashed px-6 py-12 text-center transition-colors duration-150",
          dragActive
            ? "border-accent bg-accent-soft"
            : "border-secondary/30 bg-surface hover:border-secondary/60 hover:bg-muted/40",
          disabled && "cursor-not-allowed opacity-60",
          error && !dragActive && "border-accent/60",
        )}
      >
        <span
          className={cx(
            "flex h-10 w-10 items-center justify-center rounded-[4px] border transition-colors duration-150",
            dragActive
              ? "border-accent/30 bg-surface text-accent"
              : "border-line bg-muted text-secondary",
          )}
        >
          <FileUp className="h-5 w-5" aria-hidden="true" />
        </span>
        <p className="mt-4 text-sm font-medium">
          {dragActive ? "Drop your PDF to continue" : "Drag and drop your PDF here"}
        </p>
        <p className="mt-1 text-[13px] text-secondary">
          or{" "}
          <span className="font-medium text-accent underline underline-offset-2">
            choose a file
          </span>{" "}
          from your computer
        </p>
        <p className="mt-4 text-xs text-secondary">
          PDF only · up to 20 MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          aria-label="Choose PDF file"
          onChange={handleInputChange}
          disabled={disabled}
        />
      </div>
      {error ? (
        <p role="alert" className="mt-3 text-[13px] font-medium text-accent">
          {error}
        </p>
      ) : null}
    </div>
  );
}
