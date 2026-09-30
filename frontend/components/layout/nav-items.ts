import type { PlatformId } from "@/types/api";

export interface NavItem {
  href: "/" | `/${PlatformId}`;
  label: string;
  platform?: PlatformId;
}

export const NAV_ITEMS: readonly NavItem[] = [
  { href: "/", label: "Home" },
  { href: "/instagram", label: "Instagram", platform: "instagram" },
  { href: "/tiktok", label: "TikTok", platform: "tiktok" },
  { href: "/youtube", label: "YouTube", platform: "youtube" },
];

export function isActivePath(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}
