"use client";

import { Check, Copy, Type } from "lucide-react";
import { useRef } from "react";
import { Button } from "@/components/ui/button";
import { useCopy } from "@/hooks/useCopy";

export function CaptionViewer({ caption, author }: { caption: string; author?: string | null }) {
  const box = useRef<HTMLDivElement>(null);
  const { copied, copy } = useCopy("Caption copied.");

  const selectAll = () => {
    const el = box.current;
    if (!el) return;
    const range = document.createRange();
    range.selectNodeContents(el);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
    el.focus();
  };

  return (
    <div className="space-y-3">
      {author && <p className="text-sm text-muted">Caption by {author}</p>}
      <div
        ref={box}
        tabIndex={0}
        aria-label="Caption text"
        className="max-h-72 overflow-y-auto whitespace-pre-wrap break-words rounded-xl border border-border bg-surface-2 p-4 text-[0.98rem] leading-relaxed"
      >
        {caption}
      </div>
      <div className="grid grid-cols-[1fr_auto] gap-2">
        <Button size="lg" onClick={() => void copy(caption)}>
          {copied ? <Check aria-hidden /> : <Copy aria-hidden />} {copied ? "Copied" : "Copy Caption"}
        </Button>
        <Button size="lg" variant="secondary" onClick={selectAll} aria-label="Select all caption text">
          <Type aria-hidden /> <span className="hidden sm:inline">Select All</span>
        </Button>
      </div>
      <p className="font-mono text-[0.78rem] text-muted">{caption.length.toLocaleString()} characters · not stored</p>
    </div>
  );
}
