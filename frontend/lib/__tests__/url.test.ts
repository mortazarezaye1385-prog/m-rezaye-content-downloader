import { describe, expect, it } from "vitest";
import { detectUrl, routeForDetection } from "../url";

describe("detectUrl", () => {
  it.each([
    ["https://www.instagram.com/p/C1a2B3c4D5e/", "instagram", "post"],
    ["instagram.com/reel/C9zYxWvUtS1/?igsh=1", "instagram", "reel"],
    ["https://www.instagram.com/stories/highlights/17912345678901234/", "instagram", "highlight"],
    ["https://www.tiktok.com/@some.user/video/7301234567890123456", "tiktok", "video"],
    ["https://www.tiktok.com/@some.user/photo/7301234567890123456", "tiktok", "photo"],
    ["https://vm.tiktok.com/ZMabc123/", "tiktok", "short_link"],
    ["https://youtu.be/dQw4w9WgXcQ", "youtube", "video"],
    ["https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=3", "youtube", "video"],
    ["https://youtube.com/shorts/abcdefghijk", "youtube", "short"],
  ])("detects %s", (raw: string, platform: string, kind: string) => {
    const result = detectUrl(raw);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.platform).toBe(platform);
      expect(result.kind).toBe(kind);
    }
  });

  it.each([
    ["", "empty"],
    ["   ", "empty"],
    ["hello world", "invalid"],
    ["javascript:alert(1)", "invalid"],
    ["https://user:pw@youtube.com/watch?v=dQw4w9WgXcQ", "invalid"],
    ["https://youtube.com:8443/watch?v=dQw4w9WgXcQ", "invalid"],
    ["https://vimeo.com/1234", "unsupported_platform"],
    ["https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ", "unsupported_platform"],
    ["https://www.instagram.com/someone/", "unsupported_url"],
    ["https://www.youtube.com/watch?v=nope", "invalid"],
  ])("rejects %s as %s", (raw: string, reason: string) => {
    const result = detectUrl(raw);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe(reason);
  });

  it("routes highlights to the highlight section", () => {
    const d = detectUrl("https://www.instagram.com/stories/highlights/17912345678901234/");
    if (!d.ok) throw new Error("expected ok");
    expect(routeForDetection(d, " https://www.instagram.com/stories/highlights/17912345678901234/ ")).toBe(
      "/instagram?url=https%3A%2F%2Fwww.instagram.com%2Fstories%2Fhighlights%2F17912345678901234%2F&section=highlights",
    );
  });
});
