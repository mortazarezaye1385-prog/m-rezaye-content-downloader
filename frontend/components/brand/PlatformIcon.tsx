import type { PlatformId } from "@/types/api";
import { cn } from "@/lib/cn";

/** Simplified line glyphs (not official logos) so the UI stays consistent. */
export function PlatformIcon({ platform, className }: { platform: PlatformId; className?: string }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className: cn("h-5 w-5 shrink-0", className),
    "aria-hidden": true,
  };
  if (platform === "instagram") {
    return (
      <svg {...common}>
        <rect x="3.5" y="3.5" width="17" height="17" rx="5" />
        <circle cx="12" cy="12" r="3.8" />
        <circle cx="17.2" cy="6.8" r="0.6" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (platform === "tiktok") {
    return (
      <svg {...common}>
        <path d="M14 3.5v11.2a3.8 3.8 0 1 1-3.8-3.8" />
        <path d="M14 3.5c.4 2.6 2.3 4.4 5 4.7" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <rect x="2.8" y="5.5" width="18.4" height="13" rx="4" />
      <path d="m10.3 9.3 4.4 2.7-4.4 2.7z" fill="currentColor" />
    </svg>
  );
}
