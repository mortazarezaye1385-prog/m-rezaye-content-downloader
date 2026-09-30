"use client";

import { motion } from "motion/react";
import { DownloadButton } from "@/components/progress/DownloadButton";
import { pad2 } from "@/lib/format";
import type { MediaItem } from "@/types/api";
import { MediaMeta } from "./MediaMeta";
import { MediaPreview } from "./MediaPreview";
import { MediaTypeBadge } from "./MediaTypeBadge";
import { SourceConditionNote } from "./SourceConditionNote";

export function MediaItemCard({ item, showIndex, labelPrefix = "Media" }: { item: MediaItem; showIndex: boolean; labelPrefix?: string }) {
  const name = `${labelPrefix} ${pad2(item.index + 1)}`;
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(item.index, 6) * 0.04 }}
      aria-label={name}
      className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-3"
    >
      <div className="flex items-center justify-between gap-2 px-0.5">
        {showIndex ? <span className="font-mono text-[0.85rem] font-medium text-muted">{name}</span> : <span />}
        <MediaTypeBadge type={item.kind} />
      </div>
      <MediaPreview src={item.preview_url} kind={item.kind} dimensions={item.dimensions} duration={item.duration_seconds} alt={`${name} preview`} />
      <MediaMeta item={item} />
      <SourceConditionNote condition={item.source_condition} />
      <DownloadButton ticket={item.ticket} label={item.kind === "image" ? "Download image" : "Download video"} className="mt-auto" />
    </motion.article>
  );
}
