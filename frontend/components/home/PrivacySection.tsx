import { ShieldCheck } from "lucide-react";

const LIFECYCLE = ["Link analyzed", "Media fetched to a temp folder", "Streamed to your device", "Deleted"] as const;

export function PrivacySection() {
  return (
    <section aria-labelledby="privacy-title" className="rounded-[1.5rem] border border-border bg-surface p-5 shadow-card sm:p-8">
      <div className="grid gap-6 md:grid-cols-[1.1fr_1fr] md:items-center">
        <div>
          <ShieldCheck className="h-6 w-6 text-success" aria-hidden />
          <h2 id="privacy-title" className="mt-3 font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            Your media stays temporary.
          </h2>
          <p className="mt-3 text-muted text-pretty">
            This is a personal tool, not a media library. Files only exist on the server while they&apos;re being prepared and delivered, then they&apos;re deleted.
            Links, captions and download history are never saved. Leftovers are swept on a timer and on every restart.
          </p>
        </div>
        <ol className="space-y-2.5" aria-label="What happens to a file">
          {LIFECYCLE.map((step, i) => (
            <li key={step} className="flex items-center gap-3 rounded-xl bg-surface-2 px-3.5 py-3">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-surface font-mono text-[0.8rem] ring-1 ring-border">{i + 1}</span>
              <span className={i === LIFECYCLE.length - 1 ? "font-semibold text-success" : "font-medium"}>{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
