import { PlatformIcon } from "@/components/brand/PlatformIcon";
import { Badge } from "@/components/ui/badge";
import { platformName } from "@/lib/url";
import type { PlatformId } from "@/types/api";

export function PlatformBadge({ platform }: { platform: PlatformId }) {
  return (
    <Badge>
      <PlatformIcon platform={platform} className="h-3.5 w-3.5" /> {platformName(platform)}
    </Badge>
  );
}
