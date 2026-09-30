"use client";

import { ErrorCard } from "@/components/errors/ErrorCard";

export default function RouteError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mx-auto max-w-lg py-20">
      <ErrorCard
        error={{
          code: "client_render_error",
          title: "This page hit a problem",
          message: "The interface ran into an unexpected error. Reloading the section usually fixes it.",
          retryable: true,
          request_id: error.digest ?? null,
        }}
        onRetry={reset}
      />
    </div>
  );
}
