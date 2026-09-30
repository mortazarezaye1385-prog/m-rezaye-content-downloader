import { describe, expect, it } from "vitest";
import { downloadReducer, initialDownloadState, isActive, phaseLabel, type DownloadState } from "../download-machine";
import type { JobView } from "../../types/api";

function job(partial: Partial<JobView> & Pick<JobView, "status">): JobView {
  return {
    id: "job1",
    progress: { bytes_done: 0, bytes_total: null, percent: null, determinate: false },
    items: { total: 1, succeeded: 0, failed: 0 },
    filename: null,
    notice: null,
    error: null,
    ...partial,
  };
}

describe("downloadReducer", () => {
  it("walks the full lifecycle with real numbers only", () => {
    let s: DownloadState = downloadReducer(initialDownloadState, { type: "START" });
    expect(s.phase).toBe("requesting");
    s = downloadReducer(s, { type: "JOB", job: job({ status: "preparing" }) });
    expect(s.phase).toBe("preparing");
    expect(s.percent).toBeNull();
    s = downloadReducer(s, {
      type: "JOB",
      job: job({ status: "downloading", progress: { bytes_done: 72, bytes_total: 100, percent: 72, determinate: true } }),
    });
    expect([s.phase, s.percent, s.bytesDone]).toEqual(["downloading", 72, 72]);
    s = downloadReducer(s, { type: "JOB", job: job({ status: "ready" }) });
    expect(s.phase).toBe("transferring");
    expect(phaseLabel(s)).toBe("Handing off to your browser…");
    s = downloadReducer(s, { type: "JOB", job: job({ status: "completed" }) });
    expect(s.phase).toBe("completed");
    expect(isActive(s.phase)).toBe(false);
  });

  it("ignores updates after a terminal state and for other jobs", () => {
    let s = downloadReducer(initialDownloadState, { type: "START" });
    s = downloadReducer(s, { type: "JOB", job: job({ status: "downloading" }) });
    expect(downloadReducer(s, { type: "JOB", job: job({ id: "other", status: "completed" }) }).phase).toBe("downloading");
    s = downloadReducer(s, { type: "CANCEL" });
    expect(s.phase).toBe("cancelled");
    expect(downloadReducer(s, { type: "JOB", job: job({ status: "completed" }) }).phase).toBe("cancelled");
  });

  it("surfaces server errors and expiry", () => {
    const error = { code: "network_error", title: "Network problem", message: "x", retryable: true, request_id: "r1" };
    let s = downloadReducer(initialDownloadState, { type: "START" });
    s = downloadReducer(s, { type: "JOB", job: job({ status: "failed", error }) });
    expect(s.phase).toBe("failed");
    expect(s.error?.code).toBe("network_error");
    const expired = downloadReducer(downloadReducer(initialDownloadState, { type: "START" }), { type: "JOB", job: job({ status: "expired" }) });
    expect(expired.error?.code).toBe("job_expired");
  });

  it("does not restart while active and can restart after completion", () => {
    const active = downloadReducer(initialDownloadState, { type: "START" });
    expect(downloadReducer(active, { type: "START" })).toBe(active);
    const done = { ...active, phase: "completed" as const };
    expect(downloadReducer(done, { type: "START" }).phase).toBe("requesting");
    expect(downloadReducer(done, { type: "FAIL", error: { code: "x", title: "t", message: "m", retryable: false, request_id: null } }).phase).toBe("completed");
  });
});
