"use client";

import { AlertTriangle, Clock, Link2Off, Lock, RefreshCw, ServerCrash, ShieldAlert, WifiOff } from "lucide-react";
import { motion } from "motion/react";
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import type { ApiErrorBody } from "@/types/api";

const ICONS: [RegExp, LucideIcon][] = [
  [/private|login/, Lock],
  [/invalid|unsupported_url|unsupported_platform|validation/, Link2Off],
  [/unsupported|drm/, ShieldAlert],
  [/network|unavailable_backend|client_network/, WifiOff],
  [/timeout|rate_limited|busy/, Clock],
  [/server|processing|storage|internal|bad_response|backend/, ServerCrash],
];

function iconFor(code: string): LucideIcon {
  return ICONS.find(([re]) => re.test(code))?.[1] ?? AlertTriangle;
}

interface ErrorCardProps {
  error: ApiErrorBody;
  title?: string;
  onRetry?: () => void;
  className?: string;
  compact?: boolean;
}

export function ErrorCard({ error, title, onRetry, className, compact = false }: ErrorCardProps) {
  const Icon = iconFor(error.code);
  const tone = /private|login|unsupported|drm/.test(error.code) ? "warning" : "danger";
  return (
    <motion.div
      role="alert"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex gap-3 rounded-2xl border p-4",
        tone === "warning" ? "border-warning/30 bg-warning-soft/60" : "border-danger/30 bg-danger-soft/60",
        compact && "p-3",
        className,
      )}
    >
      <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", tone === "warning" ? "text-warning" : "text-danger")} aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="font-semibold leading-snug">{title ?? error.title}</p>
        <p className="mt-1 break-words text-[0.95rem] text-muted text-pretty">{error.message}</p>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          {error.retryable && onRetry && (
            <Button variant="secondary" size="sm" onClick={onRetry}>
              <RefreshCw aria-hidden /> Try Again
            </Button>
          )}
          {error.request_id && (
            <span className="font-mono text-[0.78rem] text-muted">Ref {error.request_id}</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
