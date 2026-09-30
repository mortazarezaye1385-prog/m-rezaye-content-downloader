"use client";

import { PlatformIcon } from "@/components/brand/PlatformIcon";
import { cn } from "@/lib/cn";
import { PLATFORMS } from "@/lib/platforms";
import { detectUrl } from "@/lib/url";

/** Live, local link recognition. Says only what the URL itself reveals. */
export function DetectionReadout({ value }: { value: string }) {
  const detection = detectUrl(value);
  const detected = detection.ok ? detection.platform : null;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      <ul className="flex items-center gap-1.5" aria-label="Supported platforms">
        {PLATFORMS.map((p) => (
          <li
            key={p.id}
            className={cn(
              "grid h-8 w-8 place-items-center rounded-lg transition-all duration-200",
              detected === p.id ? p.tile : "text-muted",
              detected && detected !== p.id && "opacity-35",
            )}
            title={p.name}
          >
            <PlatformIcon platform={p.id} className="h-[1.05rem] w-[1.05rem]" />
            <span className="sr-only">{p.name}</span>
          </li>
        ))}
      </ul>
      <p aria-live="polite" className="min-w-0 font-mono text-[0.8rem] uppercase tracking-[0.08em] text-muted">
        {detection.ok ? (
          <span className="text-foreground">
            <span className="mr-1.5 inline-block h-1.5 w-1.5 -translate-y-px rounded-full bg-signal align-middle" aria-hidden />
            {detection.label}
          </span>
        ) : detection.reason === "empty" ? (
          "Instagram · TikTok · YouTube"
        ) : (
          <span className="normal-case tracking-normal text-danger">{detection.message}</span>
        )}
      </p>
    </div>
  );
}
