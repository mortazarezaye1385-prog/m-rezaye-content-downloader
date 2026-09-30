import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { DesktopNavigation } from "./DesktopNavigation";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link href="/" aria-label="M.Rezaye Content Downloader, home" className="rounded-xl">
          <Logo className="sm:hidden" compact />
          <Logo className="hidden sm:inline-flex" />
        </Link>
        <DesktopNavigation />
        <ThemeToggle />
      </div>
    </header>
  );
}
