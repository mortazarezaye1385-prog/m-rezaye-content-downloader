import Link from "next/link";
import { LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center py-24 text-center">
      <LogoMark className="h-14 w-14" />
      <h1 className="mt-6 font-display text-3xl font-semibold">Page not found</h1>
      <p className="mt-2 text-muted">That page doesn&apos;t exist.</p>
      <Button asChild className="mt-6">
        <Link href="/">Back home</Link>
      </Button>
    </div>
  );
}
