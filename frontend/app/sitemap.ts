import type { MetadataRoute } from "next";
import { SITE } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/instagram", "/tiktok", "/youtube"].map((path) => ({ url: `${SITE.url}${path}`, changeFrequency: "monthly" as const }));
}
