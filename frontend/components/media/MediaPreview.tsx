"use client";

import { Film, ImageOff, Image as ImageIcon } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { Dimensions, MediaKind } from "@/types/api";

interface MediaPreviewProps {
  src: string | null;
  kind: MediaKind;
  dimensions: Dimensions | null;
  duration?: number | null;
  alt: string;
  className?: string;
}

/** Keeps the source aspect ratio when known, never crops the media. */
export function MediaPreview({ src, kind, dimensions, duration, alt, className }: MediaPreviewProps) {
  const [failed, setFailed] = useState(false);
  const url = api.previewUrl(src);
  const ratio = dimensions ? `${dimensions.width} / ${dimensions.height}` : kind === "video" ? "9 / 16" : "4 / 5";
  const time = formatDuration(duration ?? null);
  const Fallback = failed ? ImageOff : kind === "video" ? Film : ImageIcon;

  return (
    <div
      className={cn("relative mx-auto w-full max-h-[26rem] overflow-hidden rounded-xl bg-surface-3", className)}
      style={{ aspectRatio: ratio, maxWidth: `calc(26rem * ${dimensions ? dimensions.width / dimensions.height : kind === "video" ? 9 / 16 : 4 / 5})` }}
    >
      {url && !failed ? (
        // Previews are proxied, signed thumbnails; next/image optimisation would cache them.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={url} alt={alt} loading="lazy" decoding="async" onError={() => setFailed(true)} className="h-full w-full object-contain" />
      ) : (
        <div className="grid h-full w-full place-items-center text-muted">
          <div className="flex flex-col items-center gap-2 text-sm">
            <Fallback className="h-7 w-7" aria-hidden />
            {failed ? "Preview unavailable" : "No preview provided"}
          </div>
        </div>
      )}
      {kind === "video" && time && (
        <span className="absolute bottom-2 right-2 rounded-md bg-black/70 px-1.5 py-0.5 font-mono text-[0.78rem] text-white">{time}</span>
      )}
    </div>
  );
}
