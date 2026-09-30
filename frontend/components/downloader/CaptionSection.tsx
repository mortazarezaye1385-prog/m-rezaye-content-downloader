"use client";

import { Captions } from "lucide-react";
import { useCallback } from "react";
import { ErrorCard } from "@/components/errors/ErrorCard";
import { EmptyState } from "@/components/errors/EmptyState";
import { CaptionViewer } from "@/components/media/CaptionViewer";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalyze } from "@/hooks/useAnalyze";
import { api } from "@/lib/api";
import type { CaptionResult, PlatformId } from "@/types/api";
import { AnalyzerForm } from "./AnalyzerForm";
import { SectionShell } from "./SectionShell";
import { validateForSection } from "./validators";

export function CaptionSection({ id, platform, title, placeholder }: { id: string; platform: PlatformId; title: string; placeholder: string }) {
  const fetchCaption = useCallback((url: string, signal: AbortSignal) => api.caption(platform, url, signal), [platform]);
  const state = useAnalyze<CaptionResult>(fetchCaption);
  const { run, fail } = state;

  const submit = useCallback(
    (url: string) => {
      const problem = validateForSection(url, platform, "caption");
      if (problem) fail(problem, url);
      else void run(url.trim());
    },
    [fail, platform, run],
  );

  return (
    <SectionShell id={id} title={title} description="Pull the caption text and copy it. Captions are never stored." icon={<Captions className="h-5 w-5" aria-hidden />}>
      <AnalyzerForm label={title} placeholder={placeholder} buttonLabel="Get Caption" busy={state.status === "analyzing"} onSubmit={submit} />
      <div aria-live="polite">
        {state.status === "idle" && <EmptyState title="No caption loaded" hint="Paste a post link to fetch its caption." />}
        {state.status === "analyzing" && (
          <div className="space-y-2" role="status">
            <span className="sr-only">Retrieving caption…</span>
            <Skeleton className="h-4 w-11/12" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}
        {state.status === "error" && state.error && <ErrorCard error={state.error} onRetry={() => state.lastUrl && void run(state.lastUrl)} />}
        {state.status === "success" && state.data &&
          (state.data.caption ? (
            <CaptionViewer caption={state.data.caption} author={state.data.author} />
          ) : (
            <EmptyState title="No caption found." hint="This post doesn't have caption text." />
          ))}
      </div>
    </SectionShell>
  );
}
