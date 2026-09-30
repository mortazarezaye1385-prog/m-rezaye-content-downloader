"use client";

import { DownloadButton } from "./DownloadButton";

export function DownloadAllButton({ ticket, count }: { ticket: string; count: number }) {
  return (
    <div className="rounded-2xl border border-border bg-surface-2/60 p-3 sm:p-4">
      <DownloadButton ticket={ticket} size="lg" label={`Download All (${count})`} />
      <p className="mt-2 text-center text-[0.82rem] text-muted">One ZIP, files stored as-is (no recompression). Deleted from the server right after delivery.</p>
    </div>
  );
}
