"use client";

import { CircleDashed } from "lucide-react";
import { useCallback } from "react";
import { ErrorCard } from "@/components/errors/ErrorCard";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { HIGHLIGHT_STATE_TITLES, highlightState } from "@/lib/errors";
import { MediaDownloaderSection } from "./MediaDownloaderSection";

/**
 * Always attempts retrieval. When Instagram or the retrieval method withholds
 * the Highlight, the reason is shown precisely; nothing is worked around.
 */
export function HighlightSection({ initialUrl }: { initialUrl?: string }) {
  const analyze = useCallback((url: string, signal: AbortSignal) => api.analyzeHighlight(url, signal), []);
  return (
    <MediaDownloaderSection
      id="highlights"
      platform="instagram"
      section="highlight"
      title="Instagram Highlights"
      description="Retrieve every item in a public Highlight, then download one by one or all at once."
      placeholder="Paste authorized/public Instagram Highlight URL..."
      buttonLabel="Analyze Highlight"
      analyze={analyze}
      initialUrl={initialUrl}
      icon={<CircleDashed className="h-5 w-5" aria-hidden />}
      emptyHint="Highlight links look like instagram.com/stories/highlights/…"
      itemLabel="Item"
      successBadge={(a) => <Badge variant="success">{HIGHLIGHT_STATE_TITLES.retrieved} · {a.items.length}</Badge>}
      renderError={(error, retry) => {
        const state = highlightState(error);
        return <ErrorCard error={error} title={HIGHLIGHT_STATE_TITLES[state]} onRetry={state === "temporarily_unavailable" ? retry : undefined} />;
      }}
    />
  );
}
