import { Clapperboard, Film, Image as ImageIcon, Images, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ContentType, MediaKind } from "@/types/api";

const LABELS: Record<MediaKind | ContentType, { label: string; Icon: typeof Film }> = {
  image: { label: "Image", Icon: ImageIcon },
  video: { label: "Video", Icon: Film },
  photo: { label: "Photo", Icon: ImageIcon },
  carousel: { label: "Carousel", Icon: Images },
  highlight: { label: "Highlight", Icon: Sparkles },
  short: { label: "Short", Icon: Clapperboard },
};

export function MediaTypeBadge({ type }: { type: MediaKind | ContentType }) {
  const { label, Icon } = LABELS[type];
  return (
    <Badge variant="accent">
      <Icon aria-hidden /> {label}
    </Badge>
  );
}
