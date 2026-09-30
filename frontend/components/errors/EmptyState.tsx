import type { ReactNode } from "react";
import { LogoMark } from "@/components/brand/Logo";
import { cn } from "@/lib/cn";

export function EmptyState({ title, hint, icon, className }: { title: string; hint?: string; icon?: ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center gap-3.5 rounded-2xl border border-dashed border-border-strong/70 px-4 py-4", className)}>
      <span className="opacity-70 grayscale-[35%]">{icon ?? <LogoMark className="h-8 w-8" />}</span>
      <div className="min-w-0">
        <p className="font-medium">{title}</p>
        {hint && <p className="text-sm text-muted text-pretty">{hint}</p>}
      </div>
    </div>
  );
}
