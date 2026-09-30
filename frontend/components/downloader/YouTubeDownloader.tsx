"use client";

import { MonitorPlay, RefreshCw } from "lucide-react";
import { useCallback, useState } from "react";
import { ErrorCard } from "@/components/errors/ErrorCard";
import { EmptyState } from "@/components/errors/EmptyState";
import { MediaPreview } from "@/components/media/MediaPreview";
import { DownloadButton } from "@/components/progress/DownloadButton";
import { LoadingState } from "@/components/progress/LoadingState";
import { Button } from "@/components/ui/button";
import { useAnalyze } from "@/hooks/useAnalyze";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import { canDownloadQuality, findQuality } from "@/lib/quality";
import type { MediaAnalysis } from "@/types/api";
import { AnalyzerForm } from "./AnalyzerForm";
import { QualitySelector } from "./QualitySelector";
import { SectionShell } from "./SectionShell";
import { validateForSection } from "./validators";

const ORIENTATION: Record<string, string> = { vertical: "Vertical", horizontal: "Horizontal", square: "Square" };

function Detected({ analysis }: { analysis: MediaAnalysis }) {
  const parts = [
    analysis.content_type === "short" ? "YouTube Short" : "YouTube Video",
    analysis.orientation ? `${ORIENTATION[analysis.orientation]}${analysis.aspect_ratio ? ` ${analysis.aspect_ratio}` : ""}` : null,
    formatDuration(analysis.duration_seconds),
  ].filter(Boolean);
  return (
    <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
      <p className="text-[0.72rem] font-medium uppercase tracking-[0.12em] text-muted">Detected</p>
      <p className="mt-1 font-mono text-[0.98rem]">{parts.join(" · ")}</p>
    </div>
  );
}

export function YouTubeDownloader({ initialUrl }: { initialUrl?: string }) {
  const analyze = useCallback((url: string, signal: AbortSignal) => api.analyze("youtube", url, signal), []);
  const state = useAnalyze<MediaAnalysis>(analyze);
  const { run, fail } = state;
  const [selected, setSelected] = useState<string | null>(null);
  const [staleQuality, setStaleQuality] = useState(false);

  const submit = useCallback(
    (url: string) => {
      setSelected(null);
      setStaleQuality(false);
      const problem = validateForSection(url, "youtube", "media");
      if (problem) fail(problem, url);
      else void run(url.trim());
    },
    [fail, run],
  );

  const onDownloadError = useCallback((code: string) => {
    if (code === "quality_unavailable") setStaleQuality(true);
  }, []);

  const data = state.data;
  const item = data?.items[0];
  const qualities = data?.qualities ?? [];
  const chosen = findQuality(qualities, selected);

  return (
    <SectionShell id="media" title="YouTube Downloader" description="Paste one link. See what it is and which qualities YouTube really offers, then pick one." icon={<MonitorPlay className="h-5 w-5" aria-hidden />}>
      <AnalyzerForm label="YouTube link" placeholder="Paste YouTube video or Shorts URL..." buttonLabel="Analyze Video" busy={state.status === "analyzing"} onSubmit={submit} initialValue={initialUrl} autoSubmit={Boolean(initialUrl)} />

      {state.status === "idle" && <EmptyState title="Nothing analyzed yet" hint="Works with youtube.com/watch, youtu.be and /shorts links." />}
      {state.status === "analyzing" && <LoadingState label="Analyzing video…" slowLabel="Reading available formats from YouTube…" />}
      {state.status === "error" && state.error && <ErrorCard error={state.error} onRetry={() => state.lastUrl && void run(state.lastUrl)} />}

      {state.status === "success" && data && item && (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,20rem)_1fr]">
          <div className="space-y-3">
            <MediaPreview src={item.preview_url} kind="video" dimensions={item.dimensions} duration={data.duration_seconds} alt={`${data.title ?? "Video"} thumbnail`} />
            <div className="min-w-0">
              {data.title && <p className="line-clamp-2 break-words font-display font-semibold leading-snug">{data.title}</p>}
              {data.author && <p className="truncate text-sm text-muted">{data.author}</p>}
            </div>
          </div>
          <div className="space-y-4">
            <Detected analysis={data} />
            <QualitySelector options={qualities} value={selected} onChange={(id) => { setSelected(id); setStaleQuality(false); }} />
            {staleQuality && (
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-warning-soft px-3.5 py-3 text-sm">
                <span>That quality is no longer available. Please select another available quality.</span>
                <Button variant="secondary" size="sm" onClick={() => state.lastUrl && submit(state.lastUrl)}>
                  <RefreshCw aria-hidden /> Refresh list
                </Button>
              </div>
            )}
            <DownloadButton
              key={item.ticket}
              ticket={item.ticket}
              qualityId={selected}
              size="lg"
              label={chosen ? `Download Selected Quality · ${chosen.label}` : "Download Selected Quality"}
              disabled={!canDownloadQuality(qualities, selected)}
              disabledHint="Select a quality first."
              onError={onDownloadError}
            />
            <p className="text-[0.82rem] text-muted text-pretty">
              Separate video and audio streams are joined by stream copy: no re-encoding, no upscaling. Retrieved via {data.retrieval}.
            </p>
          </div>
        </div>
      )}
    </SectionShell>
  );
}
