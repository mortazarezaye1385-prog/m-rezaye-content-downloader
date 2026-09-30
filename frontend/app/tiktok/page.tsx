import type { Metadata } from "next";
import { Suspense } from "react";
import { TikTokSections } from "@/components/downloader/TikTokSections";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionNav } from "@/components/layout/SectionNav";

export const metadata: Metadata = {
  title: "TikTok",
  description: "Download TikTok videos you're authorized to save and copy captions.",
  alternates: { canonical: "/tiktok" },
};

const SECTIONS = [
  { id: "media", label: "Photo & Video" },
  { id: "captions", label: "Captions" },
] as const;

export default function TikTokPage() {
  return (
    <div className="space-y-4">
      <PageHeader platform="tiktok" description="Videos and photo posts, served exactly as TikTok provides them." />
      <SectionNav sections={SECTIONS} />
      <Suspense>
        <TikTokSections />
      </Suspense>
    </div>
  );
}
