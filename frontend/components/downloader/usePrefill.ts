"use client";

import { useSearchParams } from "next/navigation";

/** Links handed over from Home: ?url=…&section=… (read once, never stored). */
export function usePrefill(section: string): string | undefined {
  const params = useSearchParams();
  const url = params.get("url");
  const target = params.get("section") ?? "media";
  return url && target === section ? url.slice(0, 2048) : undefined;
}
