"use client";

import { useEffect, useState } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Honest waiting state: we only say what is actually happening
 * (the request is with the platform), never fake percentages.
 */
export function LoadingState({ label = "Analyzing link…", slowLabel = "Still retrieving metadata from the platform…", rows = 1 }: { label?: string; slowLabel?: string; rows?: number }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 4000);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="space-y-4" aria-busy="true">
      <div role="status" aria-live="polite" className="flex items-center gap-3 text-[0.95rem]">
        <LogoMark className="h-7 w-7 animate-pulse motion-reduce:animate-none" />
        <span className="font-medium">{slow ? slowLabel : label}</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="space-y-3 rounded-2xl border border-border p-3">
            <Skeleton className="aspect-[4/3] w-full rounded-xl" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-11 w-full rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  );
}
