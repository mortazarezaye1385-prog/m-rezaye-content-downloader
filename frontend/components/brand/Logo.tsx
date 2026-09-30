import { cn } from "@/lib/cn";

interface LogoMarkProps {
  className?: string;
  title?: string;
}

/**
 * M.R monogram: the M's right stem doubles as the R's stem, and the period
 * drops beneath the M's valley like a download landing.
 */
export function LogoMark({ className, title }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      className={cn("h-9 w-9 shrink-0", className)}
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <defs>
        <linearGradient id="mr-logo-tile" x1="6" y1="2" x2="42" y2="46" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2a8fc6" />
          <stop offset="1" stopColor="#062e55" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="46" height="46" rx="13" fill="url(#mr-logo-tile)" />
      <rect x="1.5" y="1.5" width="45" height="45" rx="12.5" stroke="#fff" strokeOpacity="0.14" />
      <path d="M9.5 34V14l9.5 12.2L28.5 14v20" stroke="#fff" strokeWidth="3.6" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M28.5 14h4.6a5.7 5.7 0 0 1 0 11.4h-4.6M32.4 25.4 38.5 34"
        stroke="#fff"
        strokeWidth="3.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="19" cy="34" r="2.4" fill="#f1af3a" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="flex flex-col leading-none">
        <span className="font-display text-[1.05rem] font-semibold tracking-tight">
          M.Rezaye
        </span>
        {!compact && (
          <span className="mt-1 text-[0.72rem] font-medium uppercase tracking-[0.14em] text-muted">
            Content Downloader
          </span>
        )}
      </span>
    </span>
  );
}
