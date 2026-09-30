"use client";

import { usePrefill } from "./usePrefill";
import { YouTubeDownloader } from "./YouTubeDownloader";

export function YouTubeSections() {
  return <YouTubeDownloader initialUrl={usePrefill("media")} />;
}
