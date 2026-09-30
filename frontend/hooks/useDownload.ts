"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";
import { toast } from "sonner";
import { api, toErrorBody } from "@/lib/api";
import { downloadReducer, initialDownloadState, isActive } from "@/lib/download-machine";
import type { JobView } from "@/types/api";

const POLL_MS = 600;
const TERMINAL_JOB = new Set(["completed", "failed", "cancelled", "expired"]);

/** Hand the file to the browser's own download manager (streams to disk, no RAM copy). */
function triggerNativeDownload(href: string) {
  const a = document.createElement("a");
  a.href = href;
  a.rel = "noopener";
  a.download = "";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export function useDownload() {
  const [state, dispatch] = useReducer(downloadReducer, initialDownloadState);
  const jobId = useRef<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requested = useRef(false);
  const alive = useRef(true);

  const stopPolling = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);

  const handleJob = useCallback((job: JobView) => {
    dispatch({ type: "JOB", job });
    if (job.status === "ready" && !requested.current) {
      requested.current = true;
      triggerNativeDownload(api.fileUrl(job.id));
      dispatch({ type: "FILE_REQUESTED" });
    }
    if (job.status === "completed") toast.success("Download completed.", { description: job.notice ?? undefined });
    if (job.status === "failed" || job.status === "expired") toast.error("Something needs your attention.");
    return TERMINAL_JOB.has(job.status);
  }, []);

  const poll = useCallback(
    async (id: string) => {
      if (!alive.current || jobId.current !== id) return;
      try {
        const job = await api.job(id);
        if (jobId.current !== id) return;
        if (!handleJob(job)) timer.current = setTimeout(() => void poll(id), POLL_MS);
      } catch (error) {
        if (jobId.current !== id) return;
        dispatch({ type: "FAIL", error: toErrorBody(error) });
      }
    },
    [handleJob],
  );

  const start = useCallback(
    async (ticket: string, qualityId?: string | null) => {
      stopPolling();
      requested.current = false;
      jobId.current = null;
      dispatch({ type: "START" });
      try {
        const job = await api.createDownload(ticket, qualityId);
        jobId.current = job.id;
        toast("Download started.");
        if (!handleJob(job)) timer.current = setTimeout(() => void poll(job.id), POLL_MS);
      } catch (error) {
        dispatch({ type: "FAIL", error: toErrorBody(error) });
      }
    },
    [handleJob, poll, stopPolling],
  );

  const cancel = useCallback(async () => {
    const id = jobId.current;
    stopPolling();
    dispatch({ type: "CANCEL" });
    jobId.current = null;
    if (id) await api.cancel(id).catch(() => undefined); // server deletes temp files
  }, [stopPolling]);

  const reset = useCallback(() => {
    stopPolling();
    jobId.current = null;
    requested.current = false;
    dispatch({ type: "RESET" });
  }, [stopPolling]);

  /** Manual fallback if the browser blocked the automatic download. */
  const saveManually = useCallback(() => {
    if (jobId.current) triggerNativeDownload(api.fileUrl(jobId.current));
  }, []);

  // Leaving the page cancels unfinished server work so temp files are removed.
  const phaseRef = useRef(state.phase);
  phaseRef.current = state.phase;
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      stopPolling();
      const id = jobId.current;
      if (id && isActive(phaseRef.current) && !requested.current) void api.cancel(id).catch(() => undefined);
    };
  }, [stopPolling]);

  return { state, start, cancel, reset, saveManually };
}
