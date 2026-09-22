import { EXPLANATION_LEVELS, usePaper } from "../../lib/paper-context";
import { Select } from "../ui/Select";

export function DifficultySelector({
  compact = false,
  showHint = true,
}: {
  compact?: boolean;
  showHint?: boolean;
}) {
  const { explanationLevel, setExplanationLevel } = usePaper();
  const slim = compact && !showHint;

  return (
    <div className={compact ? "w-40" : "w-full sm:w-52"}>
      <Select
        id="explanation-level"
        label="Explanation level"
        slim={slim}
        value={explanationLevel}
        onChange={(e) =>
          setExplanationLevel(e.target.value as typeof explanationLevel)
        }
        hint={
          showHint
            ? (EXPLANATION_LEVELS.find((l) => l.value === explanationLevel)
                ?.hint ?? undefined)
            : undefined
        }
      >
        {EXPLANATION_LEVELS.map((level) => (
          <option key={level.value} value={level.value}>
            {level.label}
          </option>
        ))}
      </Select>
    </div>
  );
}
