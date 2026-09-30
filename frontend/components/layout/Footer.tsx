import { LogoMark } from "@/components/brand/Logo";

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-2.5">
          <LogoMark className="h-7 w-7" />
          <span>M.Rezaye Content Downloader · personal use</span>
        </div>
        <p className="max-w-md text-pretty">
          Only for content you&apos;re authorized to download. Respect each platform&apos;s terms. Nothing is bypassed, nothing is kept.
        </p>
      </div>
    </footer>
  );
}
