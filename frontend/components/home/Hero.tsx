import { LogoMark } from "@/components/brand/Logo";
import { GlobalAnalyzer } from "@/components/downloader/GlobalAnalyzer";

export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="pb-10 pt-8 sm:pb-16 sm:pt-16">
      <div className="mx-auto max-w-3xl">
        <p className="flex items-center gap-2 text-sm font-medium text-muted">
          <LogoMark className="h-6 w-6" /> M.Rezaye Content Downloader
        </p>
        <h1 id="hero-title" className="mt-5 font-display text-[2.35rem] font-semibold leading-[1.05] tracking-[-0.03em] text-balance sm:text-6xl">
          Download Your Content, <span className="text-accent">Your Way.</span>
        </h1>
        <p className="mt-4 max-w-xl text-[1.05rem] text-muted text-pretty sm:text-lg">
          Fast, clean and private media processing for Instagram, TikTok and YouTube.
        </p>
        <div className="mt-7 sm:mt-9">
          <GlobalAnalyzer />
        </div>
      </div>
    </section>
  );
}
