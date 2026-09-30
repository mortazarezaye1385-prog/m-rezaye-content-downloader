import type { Metadata } from "next";
import { Suspense } from "react";
import { YouTubeSections } from "@/components/downloader/YouTubeSections";
import { PageHeader } from "@/components/layout/PageHeader";

export const metadata: Metadata = {
  title: "YouTube",
  description: "Analyze a YouTube video or Short and download it in a quality YouTube actually offers.",
  alternates: { canonical: "/youtube" },
};

export default function YouTubePage() {
  return (
    <div className="space-y-6">
      <PageHeader platform="youtube" description="Shorts and videos. Pick from the real list of available qualities." />
      <Suspense>
        <YouTubeSections />
      </Suspense>
    </div>
  );
}
