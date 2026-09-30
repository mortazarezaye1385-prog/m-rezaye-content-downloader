"use client";

import { Clapperboard } from "lucide-react";
import { useCallback } from "react";
import { api } from "@/lib/api";
import { CaptionSection } from "./CaptionSection";
import { MediaDownloaderSection } from "./MediaDownloaderSection";
import { usePrefill } from "./usePrefill";

export function TikTokSections() {
  const mediaUrl = usePrefill("media");
  const analyze = useCallback((url: string, signal: AbortSignal) => api.analyze("tiktok", url, signal), []);
  return (
    <div className="space-y-5">
      <MediaDownloaderSection
        id="media"
        platform="tiktok"
        title="TikTok Photo & Video Downloader"
        description="Videos and photo posts. If TikTok itself offers a watermark-free rendition, that's the one you get."
        placeholder="Paste TikTok URL..."
        buttonLabel="Analyze Media"
        analyze={analyze}
        initialUrl={mediaUrl}
        icon={<Clapperboard className="h-5 w-5" aria-hidden />}
        emptyHint="Works with tiktok.com/@user/video/… and vm.tiktok.com share links."
      />
      <CaptionSection id="captions" platform="tiktok" title="TikTok Caption Copier" placeholder="Paste TikTok URL..." />
    </div>
  );
}
