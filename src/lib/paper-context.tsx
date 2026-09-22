import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ExplanationLevel =
  | "easy"
  | "intermediate"
  | "technical"
  | "research";

export const EXPLANATION_LEVELS: Array<{
  value: ExplanationLevel;
  label: string;
  hint: string;
}> = [
  { value: "easy", label: "Easy", hint: "Plain-language overview" },
  { value: "intermediate", label: "Intermediate", hint: "Undergraduate level" },
  { value: "technical", label: "Technical", hint: "Graduate level" },
  { value: "research", label: "Research", hint: "Full paper depth" },
];

export interface StagedPaper {
  name: string;
  size: number;
  lastModified: number;
}

interface PaperContextValue {
  stagedFile: File | null;
  stagedMeta: StagedPaper | null;
  explanationLevel: ExplanationLevel;
  setStagedFile: (file: File | null) => void;
  clearStagedFile: () => void;
  setExplanationLevel: (level: ExplanationLevel) => void;
}

const PaperContext = createContext<PaperContextValue | null>(null);

export function PaperProvider({ children }: { children: ReactNode }) {
  const [stagedFile, setStagedFileState] = useState<File | null>(null);
  const [explanationLevel, setExplanationLevel] =
    useState<ExplanationLevel>("intermediate");

  const setStagedFile = useCallback((file: File | null) => {
    setStagedFileState(file);
  }, []);

  const clearStagedFile = useCallback(() => {
    setStagedFileState(null);
  }, []);

  const stagedMeta: StagedPaper | null = useMemo(() => {
    if (!stagedFile) return null;
    return {
      name: stagedFile.name,
      size: stagedFile.size,
      lastModified: stagedFile.lastModified,
    };
  }, [stagedFile]);

  const value = useMemo(
    () => ({
      stagedFile,
      stagedMeta,
      explanationLevel,
      setStagedFile,
      clearStagedFile,
      setExplanationLevel,
    }),
    [
      stagedFile,
      stagedMeta,
      explanationLevel,
      setStagedFile,
      clearStagedFile,
    ],
  );

  return (
    <PaperContext.Provider value={value}>{children}</PaperContext.Provider>
  );
}

export function usePaper(): PaperContextValue {
  const ctx = useContext(PaperContext);
  if (!ctx) throw new Error("usePaper must be used within PaperProvider");
  return ctx;
}
