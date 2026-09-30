import { FeatureGrid } from "@/components/home/FeatureGrid";
import { Hero } from "@/components/home/Hero";
import { PlatformCards } from "@/components/home/PlatformCards";
import { PrivacySection } from "@/components/home/PrivacySection";

export default function HomePage() {
  return (
    <>
      <Hero />
      <PlatformCards />
      <FeatureGrid />
      <PrivacySection />
    </>
  );
}
