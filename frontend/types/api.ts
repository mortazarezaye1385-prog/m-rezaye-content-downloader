/** Mirrors backend/app/schemas/media.py and processors/jobs.py. */

export type PlatformId = "instagram" | "tiktok" | "youtube";
export type MediaKind = "image" | "video";
export type SourceCondition = "watermark_free" | "watermarked" | "unknown";
export type ContentType = "photo" | "video" | "carousel" | "highlight" | "short";
export type Orientation = "vertical" | "horizontal" | "square";

export interface Dimensions {
  width: number;
  height: number;
}

export interface QualityOption {
  id: string;
  label: string;
  tier: string | null;
  height: number;
  width: number | null;
  fps: number | null;
  hdr: boolean;
  container: string;
  video_codec: string | null;
  audio_codec: string | null;
  approx_bytes: number | null;
  requires_merge: boolean;
}

export interface MediaItem {
  index: number;
  kind: MediaKind;
  preview_url: string | null;
  dimensions: Dimensions | null;
  duration_seconds: number | null;
  format: string | null;
  approx_bytes: number | null;
  source_condition: SourceCondition;
  quality_note: string;
  ticket: string;
}

export interface MediaAnalysis {
  platform: PlatformId;
  content_type: ContentType;
  title: string | null;
  author: string | null;
  items: MediaItem[];
  bundle_ticket: string | null;
  orientation: Orientation | null;
  aspect_ratio: string | null;
  duration_seconds: number | null;
  qualities: QualityOption[] | null;
  retrieval: string;
  notices: string[];
}

export interface CaptionResult {
  platform: PlatformId;
  caption: string | null;
  author: string | null;
  retrieval: string;
}

export type JobStatus =
  | "queued"
  | "preparing"
  | "downloading"
  | "processing"
  | "ready"
  | "transferring"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

export interface ApiErrorBody {
  code: string;
  title: string;
  message: string;
  retryable: boolean;
  request_id: string | null;
}

export interface JobView {
  id: string;
  status: JobStatus;
  progress: {
    bytes_done: number;
    bytes_total: number | null;
    percent: number | null;
    determinate: boolean;
  };
  items: { total: number; succeeded: number; failed: number };
  filename: string | null;
  notice: string | null;
  error: ApiErrorBody | null;
}
