import { Loader2, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AnalyzeButton({ busy, label, busyLabel = "Analyzing…" }: { busy: boolean; label: string; busyLabel?: string }) {
  return (
    <Button type="submit" size="lg" disabled={busy} className="w-full sm:w-auto sm:min-w-44" aria-live="polite">
      {busy ? <Loader2 className="animate-spin motion-reduce:animate-none" aria-hidden /> : <ScanSearch aria-hidden />}
      {busy ? busyLabel : label}
    </Button>
  );
}
