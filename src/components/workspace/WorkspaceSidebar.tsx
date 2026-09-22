import type { LucideIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import { cx } from "../../lib/utils";
import type { NavGroup } from "./paperNav";

export interface SidebarItem {
  id: string;
  label: string;
  icon: LucideIcon;
  level?: number;
}

export function WorkspaceSidebar({
  primary,
  more = [],
  groups,
  activeId = "overview",
  disabled = false,
  disabledNote,
  mobile = false,
  onNavigate,
}: {
  primary: SidebarItem[];
  more?: SidebarItem[];
  groups?: NavGroup[];
  activeId?: string;
  disabled?: boolean;
  disabledNote?: string;
  mobile?: boolean;
  onNavigate?: (id: string) => void;
}) {
  const flatAll: SidebarItem[] = groups
    ? groups.flatMap((g) => g.entries)
    : [...primary, ...more];

  if (mobile) {
    return (
      <nav aria-label="Paper sections">
        <label
          htmlFor="workspace-section-mobile"
          className="text-[11px] font-medium tracking-wide text-secondary uppercase"
        >
          Section
        </label>
        <div className="relative mt-1">
          <select
            id="workspace-section-mobile"
            className="h-10 w-full appearance-none rounded-[4px] border border-line bg-surface pr-8 pl-3 text-sm disabled:cursor-not-allowed disabled:opacity-60"
            value={activeId}
            disabled={disabled}
            onChange={(e) => onNavigate?.(e.target.value)}
          >
            {flatAll.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
          <ChevronDown
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 right-2.5 h-4 w-4 -translate-y-1/2 text-secondary"
          />
        </div>
        {disabled && disabledNote ? (
          <p className="mt-2 text-xs text-secondary">{disabledNote}</p>
        ) : null}
      </nav>
    );
  }

  return (
    <nav aria-label="Paper sections" className="flex flex-col gap-0.5">
      {groups ? (
        groups.map((group) => (
          <div key={group.heading} className="mt-1 first:mt-0">
            <p className="px-2 pt-1 pb-2 text-[11px] font-medium tracking-wide text-secondary uppercase">
              {group.heading}
            </p>
            <ul className="flex flex-col gap-0.5">
              {group.entries.map((item) => (
                <SidebarButton
                  key={item.id}
                  item={item}
                  active={item.id === activeId}
                  disabled={disabled}
                  disabledNote={disabledNote}
                  onNavigate={onNavigate}
                />
              ))}
            </ul>
          </div>
        ))
      ) : (
        <>
          <p className="px-2 pt-1 pb-2 text-[11px] font-medium tracking-wide text-secondary uppercase">
            Paper sections
          </p>
          <ul className="flex flex-col gap-0.5">
            {primary.map((item) => (
              <SidebarButton
                key={item.id}
                item={item}
                active={item.id === activeId}
                disabled={disabled}
                disabledNote={disabledNote}
                onNavigate={onNavigate}
              />
            ))}
          </ul>
          {more.length > 0 && !disabled ? (
            <>
              <p className="px-2 pt-4 pb-2 text-[11px] font-medium tracking-wide text-secondary uppercase">
                All sections
              </p>
              <ul className="flex flex-col gap-0.5">
                {more.map((item) => (
                  <SidebarButton
                    key={item.id}
                    item={item}
                    active={item.id === activeId}
                    disabled={disabled}
                    onNavigate={onNavigate}
                  />
                ))}
              </ul>
            </>
          ) : null}
        </>
      )}
      {disabled && disabledNote ? (
        <p className="mt-3 border-t border-line px-2 pt-3 text-xs leading-relaxed text-secondary">
          {disabledNote}
        </p>
      ) : null}
    </nav>
  );
}

function SidebarButton({
  item,
  active,
  disabled,
  disabledNote,
  onNavigate,
}: {
  item: SidebarItem;
  active: boolean;
  disabled: boolean;
  disabledNote?: string;
  onNavigate?: (id: string) => void;
}) {
  const Icon = item.icon;
  const indent = Math.min(Math.max(item.level ?? 1, 1), 3);
  return (
    <li>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onNavigate?.(item.id)}
        aria-current={active && !disabled ? "page" : undefined}
        title={disabled && disabledNote ? `${item.label} — ${disabledNote}` : item.label}
        className={cx(
          "flex w-full items-center gap-2.5 rounded-[4px] px-2 py-2 text-left text-[13.5px] transition-colors duration-150",
          indent === 2 && "pl-7",
          indent >= 3 && "pl-10",
          active && !disabled
            ? "bg-accent-soft font-medium text-accent"
            : "text-secondary",
          disabled
            ? "cursor-not-allowed opacity-55"
            : "cursor-pointer hover:bg-muted hover:text-ink",
        )}
      >
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="truncate">{item.label}</span>
      </button>
    </li>
  );
}
