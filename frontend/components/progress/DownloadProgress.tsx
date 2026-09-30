"use client";

import { CheckCircle2, X } from "lucide-react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/format";
import { isActive, phaseLabel, type DownloadState } from "@/lib/download-machine";
import { cn } from "@/lib/cn";

interface DownloadProgressProps {
  state: DownloadState;
  onCancel?: () => void;
  onSaveManually?: () => void;
}

export function DownloadProgress({ state, onCancel, onSaveManually }: DownloadProgressProps) {
  const label = phaseLabel(state);
  const determinate = state.percent !== null && state.phase !== "processing";
  const percent = determinate ? Math.round(state.percent ?? 0) : null;
  const multi = state.items && state.items.total > 1;

  if (state.phase === "completed") {
    return (
      <motion.div
        role="status"
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-2.5 rounded-xl bg-success-soft px-3.5 py-3 text-success"
      >
        <CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden />
        <span className="font-semibold">Download Complete</span>
        {state.notice && <span className="min-w-0 text-sm text-foreground/80">· {state.notice}</span>}
      </motion.div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <p role="status" aria-live="polite" className="min-w-0 truncate text-[0.95rem] font-medium">
          {label}
        </p>
        {isActive(state.phase) && onCancel && state.phase !== "transferring" && (
          <Button variant="ghost" size="sm" onClick={onCancel} aria-label="Cancel download" className="-mr-2 shrink-0">
            <X aria-hidden /> Cancel
          </Button>
        )}
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent ?? undefined}
        aria-valuetext={percent === null ? "In progress, size unknown" : `${percent}%`}
        className="relative h-2.5 overflow-hidden rounded-full bg-surface-3"
      >
        {percent !== null ? (
          <div className="h-full rounded-full bg-cta transition-[width] duration-300 ease-out" style={{ width: `${Math.max(2, percent)}%` }} />
        ) : (
          <div className="mr-indeterminate absolute inset-y-0 w-2/5 rounded-full bg-cta" />
        )}
      </div>
      <div className="flex flex-wrap justify-between gap-x-3 font-mono text-[0.8rem] text-muted">
        <span>
          {percent !== null && state.bytesTotal
            ? `${formatBytes(state.bytesDone)} / ${formatBytes(state.bytesTotal)}`
            : state.bytesDone > 0
              ? `${formatBytes(state.bytesDone)} · total size not reported`
              : "Waiting for the platform…"}
        </span>
        <span className="flex gap-3">
          {multi && state.items && (
            <span>
              {state.items.succeeded + state.items.failed} of {state.items.total} items
            </span>
          )}
          {percent !== null && <span className={cn("tabular-nums text-foreground")}>{percent}%</span>}
        </span>
      </div>
      {state.phase === "transferring" && state.fileRequested && state.bytesDone === 0 && onSaveManually && (
        <p className="text-sm text-muted">
          Download didn&apos;t start?{" "}
          <button type="button" onClick={onSaveManually} className="font-medium text-accent underline underline-offset-4">
            Save file
          </button>
        </p>
      )}
    </div>
  );
}
