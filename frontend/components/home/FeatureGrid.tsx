import { Captions, Gauge, HardDriveDownload, Layers, Package, ScanEye, Smartphone, Timer } from "lucide-react";

const FEATURES = [
  { title: "Quality Detection", text: "Lists only the qualities the source really offers.", Icon: Gauge },
  { title: "Photo & Video Detection", text: "Knows a single photo from a video or a carousel.", Icon: ScanEye },
  { title: "Caption Copy", text: "Pull caption text and copy it in one tap.", Icon: Captions },
  { title: "Download Progress", text: "Real bytes and percentages, never a fake bar.", Icon: HardDriveDownload },
  { title: "Download All", text: "Every item of a carousel or Highlight in one ZIP.", Icon: Package },
  { title: "Responsive Experience", text: "Built for one-handed use on a phone first.", Icon: Smartphone },
  { title: "Temporary Processing", text: "Files exist only while they're being delivered.", Icon: Timer },
  { title: "No Persistent Media Storage", text: "No library, no history, no database.", Icon: Layers },
] as const;

export function FeatureGrid() {
  return (
    <section aria-labelledby="features-title" className="py-12 sm:py-16">
      <h2 id="features-title" className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
        Everything a downloader should do. Nothing it shouldn&apos;t.
      </h2>
      <ul className="mt-6 grid grid-cols-2 gap-x-4 gap-y-6 lg:grid-cols-4">
        {FEATURES.map(({ title, text, Icon }) => (
          <li key={title} className="min-w-0">
            <Icon className="h-5 w-5 text-accent" aria-hidden />
            <h3 className="mt-2.5 font-semibold leading-snug">{title}</h3>
            <p className="mt-1 text-[0.92rem] text-muted text-pretty">{text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
