export interface ClipboardDeps {
  clipboard?: { writeText(text: string): Promise<void> } | undefined;
  fallback?: (text: string) => boolean;
}

/** execCommand fallback for older mobile browsers / non-secure contexts. */
export function legacyCopy(text: string): boolean {
  if (typeof document === "undefined") return false;
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(area);
  return ok;
}

export async function copyText(text: string, deps: ClipboardDeps = {}): Promise<boolean> {
  if (!text) return false;
  const clipboard = "clipboard" in deps ? deps.clipboard : typeof navigator !== "undefined" ? navigator.clipboard : undefined;
  if (clipboard) {
    try {
      await clipboard.writeText(text);
      return true;
    } catch {
      // fall through to legacy path
    }
  }
  return (deps.fallback ?? legacyCopy)(text);
}
