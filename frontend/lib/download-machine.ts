/**
 * Pure state machine for one download. Progress numbers come only from the
 * server's job status; nothing is simulated.
 */
import type { ApiErrorBody, JobStatus, JobView } from "../types/api";

export type DownloadPhase =
  | "idle"
  | "requesting"
  | "preparing"
  | "downloading"
  | "processing"
  | "transferring"
  | "completed"
  | "failed"
  | "cancelled";

export interface DownloadState {
  phase: DownloadPhase;
  jobId: string | null;
  bytesDone: number;
  bytesTotal: number | null;
  percent: number | null;
  items: JobView["items"] | null;
  notice: string | null;
  filename: string | null;
  error: ApiErrorBody | null;
  fileRequested: boolean;
}

export type DownloadEvent =
  | { type: "START" }
  | { type: "JOB"; job: JobView }
  | { type: "FILE_REQUESTED" }
  | { type: "FAIL"; error: ApiErrorBody }
  | { type: "CANCEL" }
  | { type: "RESET" };

export const initialDownloadState: DownloadState = {
  phase: "idle",
  jobId: null,
  bytesDone: 0,
  bytesTotal: null,
  percent: null,
  items: null,
  notice: null,
  filename: null,
  error: null,
  fileRequested: false,
};

const TERMINAL: ReadonlySet<DownloadPhase> = new Set(["completed", "failed", "cancelled"]);

export function isTerminal(phase: DownloadPhase): boolean {
  return TERMINAL.has(phase);
}

export function isActive(phase: DownloadPhase): boolean {
  return phase !== "idle" && !TERMINAL.has(phase);
}

export function phaseFromJob(status: JobStatus): DownloadPhase {
  switch (status) {
    case "queued":
    case "preparing":
      return "preparing";
    case "downloading":
      return "downloading";
    case "processing":
      return "processing";
    case "ready":
    case "transferring":
      return "transferring";
    case "completed":
      return "completed";
    case "cancelled":
      return "cancelled";
    case "failed":
    case "expired":
      return "failed";
  }
}

export function downloadReducer(state: DownloadState, event: DownloadEvent): DownloadState {
  switch (event.type) {
    case "START":
      if (isActive(state.phase)) return state;
      return { ...initialDownloadState, phase: "requesting" };
    case "JOB": {
      if (isTerminal(state.phase)) return state;
      if (state.jobId && state.jobId !== event.job.id) return state;
      const { job } = event;
      const phase = phaseFromJob(job.status);
      const expiredError: ApiErrorBody | null =
        job.status === "expired"
          ? { code: "job_expired", title: "Download expired", message: "The temporary file expired and was deleted. Start the download again.", retryable: true, request_id: null }
          : null;
      return {
        ...state,
        phase,
        jobId: job.id,
        bytesDone: job.progress.bytes_done,
        bytesTotal: job.progress.bytes_total,
        percent: job.progress.determinate ? job.progress.percent : null,
        items: job.items,
        notice: job.notice,
        filename: job.filename,
        error: phase === "failed" ? job.error ?? expiredError : null,
      };
    }
    case "FILE_REQUESTED":
      return { ...state, fileRequested: true };
    case "FAIL":
      if (state.phase === "completed") return state;
      return { ...state, phase: "failed", error: event.error };
    case "CANCEL":
      if (!isActive(state.phase)) return state;
      return { ...state, phase: "cancelled" };
    case "RESET":
      return initialDownloadState;
  }
}

export function phaseLabel(state: DownloadState): string {
  switch (state.phase) {
    case "idle":
      return "Ready";
    case "requesting":
      return "Starting…";
    case "preparing":
      return "Preparing download…";
    case "downloading":
      return "Downloading…";
    case "processing":
      return state.items && state.items.total > 1 ? "Packaging files…" : "Finalizing file…";
    case "transferring":
      return state.bytesDone > 0 ? "Saving to your device…" : "Handing off to your browser…";
    case "completed":
      return "Download complete";
    case "failed":
      return state.error?.title ?? "Download failed";
    case "cancelled":
      return "Download cancelled";
  }
}
