import type { ApiErrorBody } from "../types/api";

export const CLIENT_ERRORS = {
  network: {
    code: "client_network",
    title: "Can't reach the server",
    message: "The processing server couldn't be reached. Check your connection or make sure the backend is running.",
    retryable: true,
    request_id: null,
  },
  timeout: {
    code: "client_timeout",
    title: "Request timed out",
    message: "The server took too long to answer. The platform may be slow right now.",
    retryable: true,
    request_id: null,
  },
  badResponse: {
    code: "client_bad_response",
    title: "Unexpected server response",
    message: "The server answered in an unexpected format. Try again in a moment.",
    retryable: true,
    request_id: null,
  },
  unavailable: {
    code: "client_backend_unavailable",
    title: "Processing server unavailable",
    message: "The app's processing server isn't responding right now. Try again shortly.",
    retryable: true,
    request_id: null,
  },
} satisfies Record<string, ApiErrorBody>;

export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.code === "string" && typeof v.title === "string" && typeof v.message === "string";
}

export function parseErrorBody(data: unknown, status: number): ApiErrorBody {
  const inner = data && typeof data === "object" ? (data as { error?: unknown }).error : undefined;
  if (isApiErrorBody(inner)) {
    return { ...inner, retryable: Boolean(inner.retryable), request_id: inner.request_id ?? null };
  }
  if (status === 502 || status === 503 || status === 504) return CLIENT_ERRORS.unavailable;
  return CLIENT_ERRORS.badResponse;
}

export function localError(title: string, message: string, code = "client_validation"): ApiErrorBody {
  return { code, title, message, retryable: false, request_id: null };
}

export type HighlightState = "retrieved" | "temporarily_unavailable" | "unsupported" | "private" | "invalid" | "removed";

const HIGHLIGHT_MAP: Record<string, Exclude<HighlightState, "retrieved">> = {
  invalid_url: "invalid",
  unsupported_url: "invalid",
  unsupported_platform: "invalid",
  validation_error: "invalid",
  client_validation: "invalid",
  private_content: "private",
  unsupported_by_provider: "unsupported",
  login_required: "unsupported",
  unsupported_content_type: "unsupported",
  provider_unavailable: "unsupported",
  drm_protected: "unsupported",
  content_deleted: "removed",
  content_unavailable: "removed",
};

export function highlightState(error: ApiErrorBody | null): HighlightState {
  if (!error) return "retrieved";
  return HIGHLIGHT_MAP[error.code] ?? "temporarily_unavailable";
}

export const HIGHLIGHT_STATE_TITLES: Record<HighlightState, string> = {
  retrieved: "Highlight retrieved",
  temporarily_unavailable: "Highlight temporarily unavailable",
  unsupported: "Not supported by the current retrieval method",
  private: "Private or restricted Highlight",
  invalid: "Invalid Highlight URL",
  removed: "Highlight unavailable or removed",
};
