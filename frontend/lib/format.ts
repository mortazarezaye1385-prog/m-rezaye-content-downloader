import type { Dimensions, QualityOption } from "../types/api";

const UNITS = ["B", "KB", "MB", "GB", "TB"] as const;

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || !Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${UNITS[unit]}`;
}

export function formatDuration(seconds: number | null | undefined): string | null {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds) || seconds < 0) return null;
  const total = Math.round(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
}

export function formatResolution(dimensions: Dimensions | null | undefined): string | null {
  if (!dimensions) return null;
  return `${dimensions.width}×${dimensions.height}`;
}

export function formatFps(fps: number | null | undefined): string | null {
  if (!fps) return null;
  return `${Math.round(fps)} fps`;
}

export function qualityDetails(option: QualityOption): string {
  const parts = [option.container.toUpperCase()];
  const fps = formatFps(option.fps);
  if (fps) parts.push(fps);
  if (option.video_codec) parts.push(option.video_codec.toUpperCase());
  if (option.hdr) parts.push("HDR");
  if (option.approx_bytes) parts.push(`≈ ${formatBytes(option.approx_bytes)}`);
  return parts.join(" · ");
}

export function pad2(n: number): string {
  return String(n).padStart(2, "0");
}
