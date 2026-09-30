import { PlatformIcon } from "@/components/brand/PlatformIcon";
import { getPlatform } from "@/lib/platforms";
import { cn } from "@/lib/cn";
import type { PlatformId } from "@/types/api";

export function PageHeader({ platform, description }: { platform: PlatformId; description: string }) {
  const config = getPlatform(platform);
  return (
    <header className="flex items-start gap-4 pt-6 sm:pt-10">
      <span className={cn("grid h-12 w-12 shrink-0 place-items-center rounded-2xl sm:h-14 sm:w-14", config.tile)}>
        <PlatformIcon platform={platform} className="h-6 w-6 sm:h-7 sm:w-7" />
      </span>
      <div className="min-w-0">
        <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">{config.name}</h1>
        <p className="mt-1.5 max-w-xl text-muted text-pretty">{description}</p>
      </div>
    </header>
  );
}
