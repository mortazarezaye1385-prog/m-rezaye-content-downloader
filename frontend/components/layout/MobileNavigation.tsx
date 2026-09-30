"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { House } from "lucide-react";
import { motion } from "motion/react";
import { PlatformIcon } from "@/components/brand/PlatformIcon";
import { cn } from "@/lib/cn";
import { NAV_ITEMS, isActivePath } from "./nav-items";

/** Thumb-reach bottom bar for phones. Hidden from md up. */
export function MobileNavigation() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/92 backdrop-blur-md md:hidden">
      <ul className="pb-safe mx-auto grid max-w-md grid-cols-4 px-2 pt-1.5">
        {NAV_ITEMS.map((item) => {
          const active = isActivePath(pathname, item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-14 flex-col items-center justify-center gap-1 rounded-xl text-[0.75rem] font-medium transition-colors",
                  active ? "text-foreground" : "text-muted",
                )}
              >
                {active && <motion.span layoutId="mobile-nav-pill" className="absolute inset-x-2 inset-y-1 rounded-xl bg-surface-2" aria-hidden />}
                <span className="relative">
                  {item.platform ? <PlatformIcon platform={item.platform} /> : <House className="h-5 w-5" aria-hidden />}
                </span>
                <span className="relative">{item.label}</span>
                {active && <span className="absolute top-1 h-1 w-1 rounded-full bg-signal" aria-hidden />}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
