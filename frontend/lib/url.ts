/**
 * Client-side link detection for instant feedback. The backend re-validates
 * everything and is the only authority; this mirrors its allowlist.
 */
import type { PlatformId } from "../types/api";

export type LinkKind =
  | "post"
  | "reel"
  | "highlight"
  | "story"
  | "video"
  | "photo"
  | "short_link"
  | "short";

export type Detection =
  | { ok: true; platform: PlatformId; kind: LinkKind; label: string }
  | { ok: false; reason: "empty" | "invalid" | "unsupported_platform" | "unsupported_url"; message: string };

export const MAX_URL_LENGTH = 2048;

const HOSTS: Record<PlatformId, readonly string[]> = {
  instagram: ["instagram.com", "www.instagram.com", "m.instagram.com"],
  tiktok: ["tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"],
  youtube: ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"],
};

const PLATFORM_NAMES: Record<PlatformId, string> = { instagram: "Instagram", tiktok: "TikTok", youtube: "YouTube" };

const KIND_LABELS: Record<LinkKind, string> = {
  post: "Post link",
  reel: "Reel link",
  highlight: "Highlight link",
  story: "Story link",
  video: "Video link",
  photo: "Photo post link",
  short_link: "Share link",
  short: "Short link",
};

const YT_ID = /^[A-Za-z0-9_-]{11}$/;

type Rule = { test: RegExp; kind: LinkKind };

const PATH_RULES: Record<PlatformId, Rule[]> = {
  instagram: [
    { test: /^\/(?:[A-Za-z0-9._]{1,30}\/)?p\/[A-Za-z0-9_-]{5,64}\/?$/, kind: "post" },
    { test: /^\/(?:[A-Za-z0-9._]{1,30}\/)?(?:reel|reels|tv)\/[A-Za-z0-9_-]{5,64}\/?$/, kind: "reel" },
    { test: /^\/stories\/highlights\/\d{5,25}\/?$/, kind: "highlight" },
    { test: /^\/s\/[A-Za-z0-9_=-]{8,200}\/?$/, kind: "highlight" },
    { test: /^\/stories\/[A-Za-z0-9._]{1,30}\/\d{5,25}\/?$/, kind: "story" },
  ],
  tiktok: [
    { test: /^\/@[A-Za-z0-9._]{2,64}\/video\/\d{8,25}\/?$/, kind: "video" },
    { test: /^\/@[A-Za-z0-9._]{2,64}\/photo\/\d{8,25}\/?$/, kind: "photo" },
    { test: /^\/t\/[A-Za-z0-9]{5,20}\/?$/, kind: "short_link" },
  ],
  youtube: [
    { test: /^\/shorts\/[A-Za-z0-9_-]{11}\/?$/, kind: "short" },
    { test: /^\/(?:live|embed|v)\/[A-Za-z0-9_-]{11}\/?$/, kind: "video" },
  ],
};

function fail(reason: Exclude<Detection, { ok: true }>["reason"], message: string): Detection {
  return { ok: false, reason, message };
}

export function toUrl(raw: string): URL | null {
  const value = raw.trim();
  if (!value || value.length > MAX_URL_LENGTH || /\s/.test(value)) return null;
  const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(value) ? value : `https://${value}`;
  try {
    const url = new URL(withScheme);
    if (!["http:", "https:"].includes(url.protocol)) return null;
    if (url.username || url.password) return null;
    if (url.port && !["80", "443"].includes(url.port)) return null;
    return url;
  } catch {
    return null;
  }
}

export function platformForHost(host: string): PlatformId | null {
  const h = host.toLowerCase().replace(/\.$/, "");
  for (const [platform, hosts] of Object.entries(HOSTS) as [PlatformId, readonly string[]][]) {
    if (hosts.includes(h)) return platform;
  }
  return null;
}

export function detectUrl(raw: string): Detection {
  if (!raw.trim()) return fail("empty", "Paste a link first.");
  const url = toUrl(raw);
  if (!url) return fail("invalid", "That doesn't look like a valid link.");
  const platform = platformForHost(url.hostname);
  if (!platform) {
    return /\.[a-z]{2,}$/i.test(url.hostname)
      ? fail("unsupported_platform", "Only Instagram, TikTok and YouTube links are supported.")
      : fail("invalid", "That doesn't look like a valid link.");
  }
  const host = url.hostname.toLowerCase();
  const path = url.pathname || "/";
  const ok = (kind: LinkKind): Detection => ({ ok: true, platform, kind, label: `${PLATFORM_NAMES[platform]} · ${KIND_LABELS[kind]}` });

  if (platform === "youtube") {
    if (host === "youtu.be") return YT_ID.test(path.replace(/^\/|\/$/g, "")) ? ok("video") : fail("unsupported_url", "Paste a link to a single YouTube video or Short.");
    if (path.replace(/\/$/, "") === "/watch") {
      return YT_ID.test(url.searchParams.get("v") ?? "") ? ok("video") : fail("invalid", "This YouTube link is missing a valid video ID.");
    }
  }
  if (platform === "tiktok" && (host === "vm.tiktok.com" || host === "vt.tiktok.com") && /^\/[A-Za-z0-9]{5,20}\/?$/.test(path)) {
    return ok("short_link");
  }
  for (const rule of PATH_RULES[platform]) {
    if (rule.test.test(path)) return ok(rule.kind);
  }
  return fail("unsupported_url", `This ${PLATFORM_NAMES[platform]} link type isn't supported. Paste a direct link to a post or video.`);
}

export function platformName(platform: PlatformId): string {
  return PLATFORM_NAMES[platform];
}

/** Where the Home analyzer should send a detected link. */
export function routeForDetection(detection: Extract<Detection, { ok: true }>, raw: string): string {
  const section = detection.platform === "instagram" && detection.kind === "highlight" ? "highlights" : "media";
  const params = new URLSearchParams({ url: raw.trim(), section });
  return `/${detection.platform}?${params.toString()}`;
}
