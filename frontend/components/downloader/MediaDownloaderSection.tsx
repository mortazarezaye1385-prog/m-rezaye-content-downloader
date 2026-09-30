"use client";

import { AnimatePresence, motion } from "motion/react";
import { useCallback, type ReactNode } from "react";
import { ErrorCard } from "@/components/errors/ErrorCard";
import { EmptyState } from "@/components/errors/EmptyState";
import { AnalysisSummary } from "@/components/media/AnalysisSummary";
import { MediaGrid } from "@/components/media/MediaGrid";
import { DownloadAllButton } from "@/components/progress/DownloadAllButton";
import { LoadingState } from "@/components/progress/LoadingState";
import { useAnalyze } from "@/hooks/useAnalyze";
import type { ApiErrorBody, MediaAnalysis, PlatformId } from "@/types/api";
import { AnalyzerForm } from "./AnalyzerForm";
import { SectionShell } from "./SectionShell";
import { validateForSection, type SectionKind } from "./validators";

interface MediaDownloaderSectionProps {
  id: string;
  platform: PlatformId;
  section?: Extract<SectionKind, "media" | "highlight">;
  title: string;
  description: string;
  placeholder: string;
  buttonLabel: string;
  analyze: (url: string, signal: AbortSignal) => Promise<MediaAnalysis>;
  initialUrl?: string;
  icon?: ReactNode;
  emptyHint: string;
  itemLabel?: string;
  /** Lets Highlights present its own state vocabulary for errors. */
  renderError?: (error: ApiErrorBody, retry: () => void) => ReactNode;
  successBadge?: (analysis: MediaAnalysis) => ReactNode;
}

export function MediaDownloaderSection(props: MediaDownloaderSectionProps) {
  const { id, platform, section = "media", analyze, initialUrl, renderError, successBadge } = props;
  const state = useAnalyze<MediaAnalysis>(analyze);
  const { run, fail } = state;

  const submit = useCallback(
    (url: string) => {
      const problem = validateForSection(url, platform, section);
      if (problem) fail(problem, url);
      else void run(url.trim());
    },
    [fail, platform, run, section],
  );

  const retry = () => state.lastUrl && void run(state.lastUrl);
  const data = state.data;

  return (
    <SectionShell id={id} title={props.title} description={props.description} icon={props.icon}>
      <AnalyzerForm
        label={props.title}
        placeholder={props.placeholder}
        buttonLabel={props.buttonLabel}
        busy={state.status === "analyzing"}
        onSubmit={submit}
        initialValue={initialUrl}
        autoSubmit={Boolean(initialUrl)}
        invalid={state.status === "error" && state.error?.code.startsWith("client_validation")}
      />
      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={state.status} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
          {state.status === "idle" && <EmptyState title="Nothing analyzed yet" hint={props.emptyHint} />}
          {state.status === "analyzing" && <LoadingState rows={section === "highlight" ? 2 : 1} />}
          {state.status === "error" && state.error && (renderError ? renderError(state.error, retry) : <ErrorCard error={state.error} onRetry={retry} />)}
          {state.status === "success" && data && (
            <div className="space-y-4">
              <AnalysisSummary analysis={data} extra={successBadge?.(data)} />
              {data.bundle_ticket && data.items.length > 1 && <DownloadAllButton ticket={data.bundle_ticket} count={data.items.length} />}
              <MediaGrid items={data.items} labelPrefix={props.itemLabel} />
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </SectionShell>
  );
}
