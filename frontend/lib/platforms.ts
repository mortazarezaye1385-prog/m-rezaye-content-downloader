import type { PlatformId } from "../types/api";

export interface PlatformConfig {
  id: PlatformId;
  name: string;
  href: `/${PlatformId}`;
  tagline: string;
  capabilities: readonly string[];
  /** Tailwind classes for the platform's icon tile. */
  tile: string;
}

export const PLATFORMS: readonly PlatformConfig[] = [
  {
    id: "instagram",
    name: "Instagram",
    href: "/instagram",
    tagline: "Posts, reels, carousels and Highlights.",
    capabilities: ["Photos", "Videos", "Highlights", "Captions"],
    tile: "bg-[oklch(0.94_0.04_20)] text-[oklch(0.5_0.16_20)] dark:bg-[oklch(0.3_0.06_20)] dark:text-[oklch(0.82_0.1_20)]",
  },
  {
    id: "tiktok",
    name: "TikTok",
    href: "/tiktok",
    tagline: "Videos, photo posts and captions.",
    capabilities: ["Photos", "Videos", "Captions"],
    tile: "bg-[oklch(0.94_0.04_195)] text-[oklch(0.45_0.09_200)] dark:bg-[oklch(0.3_0.05_200)] dark:text-[oklch(0.84_0.09_195)]",
  },
  {
    id: "youtube",
    name: "YouTube",
    href: "/youtube",
    tagline: "Shorts and videos in the quality you pick.",
    capabilities: ["Shorts", "Videos", "Quality Selection"],
    tile: "bg-[oklch(0.94_0.04_30)] text-[oklch(0.5_0.18_28)] dark:bg-[oklch(0.3_0.07_28)] dark:text-[oklch(0.8_0.12_28)]",
  },
];

export function getPlatform(id: PlatformId): PlatformConfig {
  const found = PLATFORMS.find((p) => p.id === id);
  if (!found) throw new Error(`Unknown platform ${id}`);
  return found;
}
