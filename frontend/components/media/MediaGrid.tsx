import type { MediaItem } from "@/types/api";
import { cn } from "@/lib/cn";
import { MediaItemCard } from "./MediaItemCard";

export function MediaGrid({ items, labelPrefix }: { items: MediaItem[]; labelPrefix?: string }) {
  const single = items.length === 1;
  return (
    <div className={cn("grid gap-3", single ? "mx-auto max-w-md" : "sm:grid-cols-2 lg:grid-cols-3")}>
      {items.map((item) => (
        <MediaItemCard key={item.ticket} item={item} showIndex={!single} labelPrefix={labelPrefix} />
      ))}
    </div>
  );
}
