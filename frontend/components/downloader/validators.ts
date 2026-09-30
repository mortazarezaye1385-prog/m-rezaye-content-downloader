import { localError } from "@/lib/errors";
import { detectUrl, platformName } from "@/lib/url";
import type { ApiErrorBody, PlatformId } from "@/types/api";

export type SectionKind = "media" | "caption" | "highlight";

/** Local pre-check so obviously wrong links never hit the server. */
export function validateForSection(raw: string, platform: PlatformId, section: SectionKind): ApiErrorBody | null {
  const d = detectUrl(raw);
  if (!d.ok) {
    const title = d.reason === "unsupported_platform" ? "Unsupported platform" : d.reason === "unsupported_url" ? "Unsupported link" : "Invalid URL";
    return localError(title, d.message);
  }
  if (d.platform !== platform) {
    return localError("Wrong page for this link", `This is a ${platformName(d.platform)} link. Open the ${platformName(d.platform)} page to use it.`);
  }
  if (platform === "instagram") {
    if (section === "highlight" && d.kind !== "highlight") {
      return localError("Invalid Highlight URL", "Highlight links look like instagram.com/stories/highlights/…");
    }
    if (section !== "highlight" && d.kind === "highlight") {
      return localError("That's a Highlight link", "Use the Highlights section below for Highlight links.");
    }
    if (d.kind === "story") {
      return localError("Unsupported content type", "Individual stories aren't supported. Paste a post, reel or Highlight link.");
    }
  }
  return null;
}
