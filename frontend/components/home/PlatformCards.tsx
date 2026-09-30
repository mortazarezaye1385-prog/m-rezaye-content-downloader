import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { PlatformIcon } from "@/components/brand/PlatformIcon";
import { cn } from "@/lib/cn";
import { PLATFORMS } from "@/lib/platforms";

export function PlatformCards() {
  return (
    <section aria-labelledby="platforms-title" className="py-6">
      <h2 id="platforms-title" className="sr-only">Platforms</h2>
      <ul className="grid gap-3 md:grid-cols-3">
        {PLATFORMS.map((p) => (
          <li key={p.id}>
            <Link
              href={p.href}
              className="group flex h-full items-start gap-4 rounded-[var(--radius-card)] border border-border bg-surface p-4 shadow-card transition-[border-color,transform] duration-200 hover:-translate-y-0.5 hover:border-border-strong sm:p-5 md:flex-col"
            >
              <span className={cn("grid h-12 w-12 shrink-0 place-items-center rounded-2xl", p.tile)}>
                <PlatformIcon platform={p.id} className="h-6 w-6" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center justify-between gap-2">
                  <span className="font-display text-lg font-semibold">{p.name}</span>
                  <ArrowUpRight className="h-5 w-5 text-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-foreground" aria-hidden />
                </span>
                <span className="mt-0.5 block text-[0.95rem] text-muted">{p.tagline}</span>
                <span className="mt-3 flex flex-wrap gap-1.5">
                  {p.capabilities.map((c) => (
                    <span key={c} className="rounded-md bg-surface-2 px-2 py-1 text-[0.8rem] font-medium">
                      {c}
                    </span>
                  ))}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
