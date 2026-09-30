"use client";

import { Images } from "lucide-react";
import { useCallback } from "react";
import { api } from "@/lib/api";
import { CaptionSection } from "./CaptionSection";
import { HighlightSection } from "./HighlightSection";
import { MediaDownloaderSection } from "./MediaDownloaderSection";
import { usePrefill } from "./usePrefill";

export function InstagramSections() {
  const mediaUrl = usePrefill("media");
  const highlightUrl = usePrefill("highlights");
  const analyze = useCallback((url: string, signal: AbortSignal) => api.analyze("instagram", url, signal), []);
  return (
    <div className="space-y-5">
      <MediaDownloaderSection
        id="media"
        platform="instagram"
        title="Instagram Photo & Video Downloader"
        description="Posts, reels and carousels. Every item is shown with what the source actually provides."
        placeholder="Paste Instagram post URL..."
        buttonLabel="Analyze Media"
        analyze={analyze}
        initialUrl={mediaUrl}
        icon={<Images className="h-5 w-5" aria-hidden />}
        emptyHint="Paste a post or reel link to see its media."
      />
      <CaptionSection id="captions" platform="instagram" title="Instagram Caption Copier" placeholder="Paste Instagram post URL..." />
      <HighlightSection initialUrl={highlightUrl} />
    </div>
  );
}
