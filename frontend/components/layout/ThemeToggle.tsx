"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

const OPTIONS = [
  { value: "system", label: "System theme", Icon: Monitor },
  { value: "light", label: "Light theme", Icon: Sun },
  { value: "dark", label: "Dark theme", Icon: Moon },
] as const;

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div role="radiogroup" aria-label="Color theme" className={cn("inline-flex rounded-xl border border-border bg-surface-2 p-0.5", className)}>
      {OPTIONS.map(({ value, label, Icon }) => {
        const active = mounted && theme === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={() => setTheme(value)}
            className={cn(
              "grid h-9 w-9 place-items-center rounded-[0.6rem] text-muted transition-colors hover:text-foreground",
              active && "bg-surface text-foreground shadow-sm ring-1 ring-border",
            )}
          >
            <Icon className="h-[1.05rem] w-[1.05rem]" aria-hidden />
          </button>
        );
      })}
    </div>
  );
}
