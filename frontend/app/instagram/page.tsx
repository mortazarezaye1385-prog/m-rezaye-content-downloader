import type { Metadata } from "next";
import { Suspense } from "react";
import { InstagramSections } from "@/components/downloader/InstagramSections";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionNav } from "@/components/layout/SectionNav";

export const metadata: Metadata = {
  title: "Instagram",
  description: "Download photos, videos, carousels and Highlights you're authorized to save, and copy captions.",
  alternates: { canonical: "/instagram" },
};

const SECTIONS = [
  { id: "media", label: "Photo & Video" },
  { id: "captions", label: "Captions" },
  { id: "highlights", label: "Highlights" },
] as const;

export default function InstagramPage() {
  return (
    <div className="space-y-4">
      <PageHeader platform="instagram" description="Posts, reels, carousels and Highlights, in the highest quality the source provides." />
      <SectionNav sections={SECTIONS} />
      <Suspense>
        <InstagramSections />
      </Suspense>
    </div>
  );
}
