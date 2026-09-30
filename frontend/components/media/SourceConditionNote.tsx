import { BadgeCheck, Info, Stamp } from "lucide-react";
import type { SourceCondition } from "@/types/api";

const COPY: Record<SourceCondition, { text: string; Icon: typeof Info; className: string }> = {
  watermark_free: { text: "Watermark-free source available", Icon: BadgeCheck, className: "text-success" },
  watermarked: { text: "Source only provides a watermarked version", Icon: Stamp, className: "text-warning" },
  unknown: { text: "Highest available quality · served as the source provides it", Icon: Info, className: "text-muted" },
};

export function SourceConditionNote({ condition }: { condition: SourceCondition }) {
  const { text, Icon, className } = COPY[condition];
  return (
    <p className={`flex items-start gap-1.5 text-[0.84rem] ${className}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span>{text}</span>
    </p>
  );
}
