"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

export interface SectionLink {
  id: string;
  label: string;
}

/** Sticky in-page switcher so each section is one tap away on a phone. */
export function SectionNav({ sections }: { sections: readonly SectionLink[] }) {
  const [active, setActive] = useState(sections[0]?.id ?? "");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-120px 0px -55% 0px" },
    );
    sections.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [sections]);

  if (sections.length < 2) return null;

  return (
    <nav aria-label="Sections" className="sticky top-16 z-30 -mx-4 bg-background/85 px-4 py-3 backdrop-blur-md sm:mx-0 sm:px-0">
      <ul className="flex gap-2 overflow-x-auto [scrollbar-width:none]">
        {sections.map((s) => (
          <li key={s.id}>
            <a
              href={`#${s.id}`}
              aria-current={active === s.id ? "true" : undefined}
              className={cn(
                "inline-flex h-10 items-center rounded-full border px-4 text-sm font-medium transition-colors",
                active === s.id ? "border-transparent bg-foreground text-background" : "border-border text-muted hover:text-foreground",
              )}
            >
              {s.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
