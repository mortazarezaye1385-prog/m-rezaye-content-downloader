"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { detectUrl, routeForDetection } from "@/lib/url";
import { AnalyzerForm } from "./AnalyzerForm";
import { DetectionReadout } from "./DetectionReadout";

/** Home analyzer: recognise the platform, then hand off to its page, which calls the backend. */
export function GlobalAnalyzer() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    (raw: string) => {
      const detection = detectUrl(raw);
      if (!detection.ok) {
        setError(detection.message);
        return;
      }
      setError(null);
      setBusy(true);
      router.push(routeForDetection(detection, raw));
    },
    [router],
  );

  return (
    <AnalyzerForm
      label="Supported link"
      placeholder="Paste a supported URL..."
      buttonLabel="Analyze"
      busy={busy}
      onSubmit={submit}
      invalid={Boolean(error)}
      hint={(value) =>
        error && !value ? <p role="alert" className="text-sm text-danger">{error}</p> : <DetectionReadout value={value} />
      }
    />
  );
}
