"use client";

import { MotionConfig } from "motion/react";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import type { ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
      <MotionConfig reducedMotion="user" transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}>
        {children}
        <Toaster
          position="top-center"
          theme="system"
          visibleToasts={2}
          toastOptions={{
            classNames: {
              toast: "!rounded-xl !border !border-border !bg-surface !text-foreground !shadow-card !font-sans",
              description: "!text-muted",
            },
          }}
        />
      </MotionConfig>
    </ThemeProvider>
  );
}
