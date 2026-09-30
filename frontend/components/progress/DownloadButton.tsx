"use client";

import { Download, RotateCcw } from "lucide-react";
import { useEffect, useId, type ReactNode } from "react";
import { ErrorCard } from "@/components/errors/ErrorCard";
import { Button } from "@/components/ui/button";
import { useDownload } from "@/hooks/useDownload";
import { isActive } from "@/lib/download-machine";
import { cn } from "@/lib/cn";
import { DownloadProgress } from "./DownloadProgress";

interface DownloadButtonProps {
  ticket: string;
  qualityId?: string | null;
  label?: ReactNode;
  disabled?: boolean;
  disabledHint?: string;
  size?: "md" | "lg";
  className?: string;
  onError?: (code: string) => void;
}

/** One button that owns one real download from request to completion. */
export function DownloadButton({ ticket, qualityId, label = "Download", disabled, disabledHint, size = "md", className, onError }: DownloadButtonProps) {
  const { state, start, cancel, reset, saveManually } = useDownload();
  const hintId = useId();
  const begin = () => void start(ticket, qualityId);
  const failedCode = state.phase === "failed" ? state.error?.code : undefined;

  useEffect(() => {
    if (failedCode && onError) onError(failedCode);
  }, [failedCode, onError]);

  if (isActive(state.phase) || state.phase === "completed") {
    return (
      <div className={cn("space-y-2", className)}>
        <DownloadProgress state={state} onCancel={cancel} onSaveManually={saveManually} />
        {state.phase === "completed" && (
          <Button variant="ghost" size="sm" onClick={reset} className="-ml-2">
            <RotateCcw aria-hidden /> Download again
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {state.phase === "failed" && state.error && <ErrorCard error={state.error} onRetry={begin} compact />}
      {state.phase === "cancelled" && <p className="text-sm text-muted" role="status">Cancelled. Temporary files were removed.</p>}
      <Button size={size} className="w-full" onClick={begin} disabled={disabled} aria-describedby={disabled && disabledHint ? hintId : undefined}>
        <Download aria-hidden /> {label}
      </Button>
      {disabled && disabledHint && (
        <p id={hintId} className="text-center text-sm text-muted">
          {disabledHint}
        </p>
      )}
    </div>
  );
}
