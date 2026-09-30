import type { Metadata, Viewport } from "next";
import { Hind, JetBrains_Mono, Poppins } from "next/font/google";
import type { ReactNode } from "react";
import { Footer } from "@/components/layout/Footer";
import { MobileNavigation } from "@/components/layout/MobileNavigation";
import { Providers } from "@/components/layout/Providers";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SITE } from "@/lib/site";
import "./globals.css";

const heading = Poppins({ subsets: ["latin"], weight: ["500", "600", "700"], variable: "--font-heading", display: "swap" });
const body = Hind({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body", display: "swap" });
const code = JetBrains_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-code", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.name, template: `%s · ${SITE.name}` },
  description: SITE.description,
  applicationName: SITE.name,
  appleWebApp: { title: SITE.shortName, statusBarStyle: "black-translucent" },
  openGraph: { type: "website", siteName: SITE.name, title: SITE.name, description: SITE.description, images: [{ url: "/og.png", width: 1200, height: 630, alt: SITE.name }] },
  twitter: { card: "summary_large_image", title: SITE.name, description: SITE.description, images: ["/og.png"] },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0f141c" },
    { media: "(prefers-color-scheme: light)", color: "#f7f9fc" },
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${heading.variable} ${body.variable} ${code.variable}`}>
      <body className="bg-app-glow min-h-dvh antialiased">
        <Providers>
          <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-4 focus:py-2">
            Skip to content
          </a>
          <SiteHeader />
          <main id="main" className="mx-auto w-full max-w-6xl px-4 pb-32 sm:px-6 md:pb-16">
            {children}
          </main>
          <div className="pb-20 md:pb-0">
            <Footer />
          </div>
          <MobileNavigation />
        </Providers>
      </body>
    </html>
  );
}
