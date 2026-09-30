import { describe, expect, it, vi } from "vitest";
import { copyText } from "../clipboard";
import { CLIENT_ERRORS, highlightState, parseErrorBody } from "../errors";
import { formatBytes, formatDuration, qualityDetails } from "../format";
import { canDownloadQuality, reconcileSelection } from "../quality";
import type { QualityOption } from "../../types/api";

const q = (id: string, height: number): QualityOption => ({
  id, label: id, tier: null, height, width: null, fps: 30, hdr: false, container: "mp4",
  video_codec: "avc1", audio_codec: "mp4a", approx_bytes: 12_400_000, requires_merge: true,
});

describe("format", () => {
  it("formats bytes and durations", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(12.4 * 1024 * 1024)).toBe("12.4 MB");
    expect(formatBytes(null)).toBe("—");
    expect(formatDuration(32)).toBe("00:32");
    expect(formatDuration(222)).toBe("03:42");
    expect(formatDuration(3723)).toBe("1:02:03");
    expect(formatDuration(null)).toBeNull();
    expect(qualityDetails(q("1080p", 1080))).toBe("MP4 · 30 fps · AVC1 · ≈ 11.8 MB");
  });
});

describe("quality selection", () => {
  const options = [q("1080p", 1080), q("720p", 720)];
  it("requires an explicit, existing selection", () => {
    expect(canDownloadQuality(options, null)).toBe(false);
    expect(canDownloadQuality(options, "1080p")).toBe(true);
    expect(canDownloadQuality(options, "2160p")).toBe(false);
    expect(reconcileSelection([q("720p", 720)], "1080p")).toBeNull();
    expect(reconcileSelection(options, "720p")).toBe("720p");
  });
});

describe("errors", () => {
  it("keeps server error bodies and falls back honestly", () => {
    const body = { error: { code: "private_content", title: "Private content", message: "m", retryable: false, request_id: "abc" } };
    expect(parseErrorBody(body, 403).code).toBe("private_content");
    expect(parseErrorBody("<html>", 502)).toEqual(CLIENT_ERRORS.unavailable);
    expect(parseErrorBody(null, 400)).toEqual(CLIENT_ERRORS.badResponse);
  });

  it("maps highlight states", () => {
    const e = (code: string) => ({ code, title: "", message: "", retryable: false, request_id: null });
    expect(highlightState(null)).toBe("retrieved");
    expect(highlightState(e("private_content"))).toBe("private");
    expect(highlightState(e("unsupported_by_provider"))).toBe("unsupported");
    expect(highlightState(e("invalid_url"))).toBe("invalid");
    expect(highlightState(e("upstream_rate_limited"))).toBe("temporarily_unavailable");
    expect(highlightState(e("client_network"))).toBe("temporarily_unavailable");
  });
});

describe("copyText", () => {
  it("uses the async clipboard when available", async () => {
    const writeText = vi.fn(async () => undefined);
    expect(await copyText("hello", { clipboard: { writeText } })).toBe(true);
    expect(writeText).toHaveBeenCalledWith("hello");
  });

  it("falls back when the clipboard API rejects or is missing", async () => {
    const fallback = vi.fn(() => true);
    const writeText = vi.fn(async () => { throw new Error("denied"); });
    expect(await copyText("hi", { clipboard: { writeText }, fallback })).toBe(true);
    expect(await copyText("hi", { clipboard: undefined, fallback })).toBe(true);
    expect(fallback).toHaveBeenCalledTimes(2);
  });

  it("refuses empty text", async () => {
    expect(await copyText("", { clipboard: undefined, fallback: () => true })).toBe(false);
  });
});
