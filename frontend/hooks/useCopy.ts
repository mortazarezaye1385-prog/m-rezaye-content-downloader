"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { copyText } from "@/lib/clipboard";

export function useCopy(successMessage = "Copied.") {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const copy = useCallback(
    async (text: string) => {
      const ok = await copyText(text);
      if (ok) {
        setCopied(true);
        toast.success(successMessage);
        if (timer.current) clearTimeout(timer.current);
        timer.current = setTimeout(() => setCopied(false), 1800);
      } else {
        toast.error("Couldn't copy. Select the text and copy it manually.");
      }
      return ok;
    },
    [successMessage],
  );

  return { copied, copy };
}
