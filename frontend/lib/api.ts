import { CLIENT_ERRORS, parseErrorBody } from "./errors";
import type { ApiErrorBody, CaptionResult, JobView, MediaAnalysis, PlatformId } from "../types/api";

/** Empty = same origin (Next.js rewrites /api/* to the backend). */
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "").replace(/\/$/, "");
const ANALYZE_TIMEOUT_MS = 70_000;
const DEFAULT_TIMEOUT_MS = 20_000;

export class ApiError extends Error {
  readonly body: ApiErrorBody;
  readonly status: number;

  constructor(body: ApiErrorBody, status: number) {
    super(body.message);
    this.name = "ApiError";
    this.body = body;
    this.status = status;
  }
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
}

async function request<T>(path: string, { method = "GET", body, signal, timeoutMs = DEFAULT_TIMEOUT_MS }: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { "content-type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
      cache: "no-store",
    });
  } catch (error) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    throw new ApiError(timedOut ? CLIENT_ERRORS.timeout : CLIENT_ERRORS.network, 0);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }

  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(parseErrorBody(data, response.status), response.status);
  if (data === null) throw new ApiError(CLIENT_ERRORS.badResponse, response.status);
  return data as T;
}

export function toErrorBody(error: unknown): ApiErrorBody {
  if (error instanceof ApiError) return error.body;
  return CLIENT_ERRORS.badResponse;
}

export const api = {
  analyze(platform: PlatformId, url: string, signal?: AbortSignal) {
    return request<MediaAnalysis>(`/api/${platform}/analyze`, { method: "POST", body: { url }, signal, timeoutMs: ANALYZE_TIMEOUT_MS });
  },
  analyzeHighlight(url: string, signal?: AbortSignal) {
    return request<MediaAnalysis>("/api/instagram/highlight", { method: "POST", body: { url }, signal, timeoutMs: ANALYZE_TIMEOUT_MS });
  },
  caption(platform: PlatformId, url: string, signal?: AbortSignal) {
    return request<CaptionResult>(`/api/${platform}/caption`, { method: "POST", body: { url }, signal, timeoutMs: ANALYZE_TIMEOUT_MS });
  },
  createDownload(ticket: string, qualityId?: string | null) {
    return request<JobView>("/api/downloads", { method: "POST", body: { ticket, quality_id: qualityId ?? null }, timeoutMs: ANALYZE_TIMEOUT_MS });
  },
  job(id: string) {
    return request<JobView>(`/api/downloads/${encodeURIComponent(id)}`);
  },
  cancel(id: string) {
    return request<JobView>(`/api/downloads/${encodeURIComponent(id)}`, { method: "DELETE" });
  },
  fileUrl(id: string) {
    return `${API_BASE}/api/downloads/${encodeURIComponent(id)}/file`;
  },
  previewUrl(path: string | null) {
    if (!path) return null;
    return path.startsWith("/api/") ? `${API_BASE}${path}` : null;
  },
};
