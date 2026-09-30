"use client";

import { ClipboardPaste, X } from "lucide-react";
import { forwardRef, useId } from "react";
import { cn } from "@/lib/cn";

interface UrlInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label: string;
  busy?: boolean;
  invalid?: boolean;
  describedBy?: string;
  autoFocus?: boolean;
}

/**
 * The signature element: a viewfinder. Frame corners brighten to signal amber
 * on focus and tighten while a link is being analyzed.
 */
export const UrlInput = forwardRef<HTMLInputElement, UrlInputProps>(function UrlInput(
  { value, onChange, placeholder, label, busy, invalid, describedBy, autoFocus },
  ref,
) {
  const id = useId();
  const paste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) onChange(text.trim());
    } catch {
      // Permission denied or unsupported: the user can still long-press to paste.
    }
  };

  return (
    <div className="group/vf relative" data-busy={busy ? "" : undefined} data-invalid={invalid ? "" : undefined}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      {(["left-0 top-0 border-l-2 border-t-2 rounded-tl-xl", "right-0 top-0 border-r-2 border-t-2 rounded-tr-xl", "bottom-0 left-0 border-b-2 border-l-2 rounded-bl-xl", "bottom-0 right-0 border-b-2 border-r-2 rounded-br-xl"] as const).map((pos) => (
        <span
          key={pos}
          aria-hidden
          className={cn(
            "pointer-events-none absolute h-4 w-4 border-border-strong transition-all duration-200",
            "group-focus-within/vf:border-signal group-data-[busy]/vf:border-signal group-data-[invalid]/vf:border-danger",
            "group-data-[busy]/vf:m-1",
            pos,
          )}
        />
      ))}
      <div className="flex items-center gap-1 rounded-2xl border border-border bg-surface p-1.5 shadow-card transition-colors group-focus-within/vf:border-border-strong">
        <input
          ref={ref}
          id={id}
          type="url"
          inputMode="url"
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          enterKeyHint="go"
          autoFocus={autoFocus}
          value={value}
          maxLength={2048}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          className="h-12 min-w-0 flex-1 bg-transparent px-3 text-base outline-none placeholder:text-muted/80 focus-visible:outline-none"
        />
        {value ? (
          <button type="button" onClick={() => onChange("")} aria-label="Clear link" className="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-muted hover:bg-surface-2 hover:text-foreground">
            <X className="h-5 w-5" aria-hidden />
          </button>
        ) : (
          <button type="button" onClick={() => void paste()} aria-label="Paste link from clipboard" className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl px-3 text-sm font-medium text-muted hover:bg-surface-2 hover:text-foreground">
            <ClipboardPaste className="h-[1.1rem] w-[1.1rem]" aria-hidden /> Paste
          </button>
        )}
      </div>
    </div>
  );
});
