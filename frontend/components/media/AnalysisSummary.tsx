import { Info } from "lucide-react";
import type { ReactNode } from "react";
import type { MediaAnalysis } from "@/types/api";
import { MediaTypeBadge } from "./MediaTypeBadge";
import { PlatformBadge } from "./PlatformBadge";

export function AnalysisSummary({ analysis, extra }: { analysis: MediaAnalysis; extra?: ReactNode }) {
  const count = analysis.items.length;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <PlatformBadge platform={analysis.platform} />
        <MediaTypeBadge type={analysis.content_type} />
        {count > 1 && <span className="text-sm text-muted">{count} items</span>}
        {extra}
      </div>
      {(analysis.title || analysis.author) && (
        <div className="min-w-0">
          {analysis.title && <p className="line-clamp-2 break-words font-display font-semibold leading-snug">{analysis.title}</p>}
          {analysis.author && <p className="truncate text-sm text-muted">{analysis.author}</p>}
        </div>
      )}
      {analysis.notices.length > 0 && (
        <ul className="space-y-1.5">
          {analysis.notices.map((notice) => (
            <li key={notice} className="flex gap-2 text-[0.85rem] text-muted">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              <span className="text-pretty">{notice}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-[0.78rem] text-muted">Retrieved via {analysis.retrieval}</p>
    </div>
  );
}
