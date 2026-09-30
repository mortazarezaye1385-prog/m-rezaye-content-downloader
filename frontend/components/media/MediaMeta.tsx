import { formatBytes, formatDuration, formatResolution } from "@/lib/format";
import type { MediaItem } from "@/types/api";

/** Rangefinder-style readout. Only fields the source actually reported. */
export function MediaMeta({ item }: { item: MediaItem }) {
  const rows: [string, string][] = [];
  const res = formatResolution(item.dimensions);
  rows.push(["Resolution", res ?? "Not reported"]);
  if (item.format) rows.push(["Format", item.format.toUpperCase()]);
  const duration = formatDuration(item.duration_seconds);
  if (item.kind === "video" && duration) rows.push(["Duration", duration]);
  if (item.approx_bytes) rows.push(["Size", `≈ ${formatBytes(item.approx_bytes)}`]);
  return (
    <dl className="grid grid-cols-2 gap-x-3 gap-y-2 rounded-xl bg-surface-2 px-3 py-2.5">
      {rows.map(([k, v]) => (
        <div key={k} className="min-w-0">
          <dt className="text-[0.72rem] font-medium uppercase tracking-[0.1em] text-muted">{k}</dt>
          <dd className="truncate font-mono text-[0.88rem]">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
