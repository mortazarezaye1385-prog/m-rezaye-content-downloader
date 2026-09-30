"use client";

import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { AnalyzeButton } from "./AnalyzeButton";
import { UrlInput } from "./UrlInput";

interface AnalyzerFormProps {
  placeholder: string;
  buttonLabel: string;
  label: string;
  busy: boolean;
  onSubmit: (url: string) => void;
  initialValue?: string;
  autoSubmit?: boolean;
  hint?: (value: string) => ReactNode;
  invalid?: boolean;
}

export function AnalyzerForm({ placeholder, buttonLabel, label, busy, onSubmit, initialValue = "", autoSubmit, hint, invalid }: AnalyzerFormProps) {
  const [value, setValue] = useState(initialValue);
  const hintId = useId();
  const submitted = useRef(false);

  useEffect(() => {
    if (autoSubmit && initialValue && !submitted.current) {
      submitted.current = true;
      onSubmit(initialValue);
    }
  }, [autoSubmit, initialValue, onSubmit]);

  const handle = (e: FormEvent) => {
    e.preventDefault();
    if (!busy) onSubmit(value);
  };

  return (
    <form onSubmit={handle} noValidate className="space-y-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="min-w-0 flex-1">
          <UrlInput value={value} onChange={setValue} placeholder={placeholder} label={label} busy={busy} invalid={invalid} describedBy={hint ? hintId : undefined} />
        </div>
        <AnalyzeButton busy={busy} label={buttonLabel} />
      </div>
      {hint && (
        <div id={hintId} className="min-h-6">
          {hint(value)}
        </div>
      )}
    </form>
  );
}
