"use client";

import { cn } from "@/lib/cn";
import { qualityDetails } from "@/lib/format";
import type { QualityOption } from "@/types/api";

interface QualitySelectorProps {
  options: QualityOption[];
  value: string | null;
  onChange: (id: string) => void;
  disabled?: boolean;
}

/** Native radio group: only qualities the platform actually offers, nothing pre-selected. */
export function QualitySelector({ options, value, onChange, disabled }: QualitySelectorProps) {
  return (
    <fieldset disabled={disabled} className="space-y-2.5">
      <legend className="mb-2 text-sm font-semibold">Available Quality</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((option) => {
          const checked = option.id === value;
          return (
            <label
              key={option.id}
              className={cn(
                "relative flex min-h-16 cursor-pointer items-center gap-3 rounded-xl border px-3.5 py-3 transition-colors",
                checked ? "border-accent bg-accent-soft/70" : "border-border bg-surface hover:border-border-strong",
                "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-ring",
                disabled && "cursor-not-allowed opacity-60",
              )}
            >
              <input type="radio" name="quality" value={option.id} checked={checked} onChange={() => onChange(option.id)} className="peer sr-only" />
              <span
                aria-hidden
                className={cn("grid h-5 w-5 shrink-0 place-items-center rounded-full border-2", checked ? "border-accent" : "border-border-strong")}
              >
                {checked && <span className="h-2.5 w-2.5 rounded-full bg-accent" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline gap-2">
                  <span className="font-mono text-[1.05rem] font-medium">{option.label}</span>
                  {option.tier && <span className="text-sm font-medium text-muted">{option.tier}</span>}
                </span>
                <span className="block truncate font-mono text-[0.76rem] text-muted">{qualityDetails(option)}</span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
