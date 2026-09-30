import type { ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function SectionShell({ id, title, description, children, icon }: { id: string; title: string; description: string; children: ReactNode; icon?: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-32">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            {icon && <span className="text-accent">{icon}</span>}
            <CardTitle id={`${id}-title`}>{title}</CardTitle>
          </div>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">{children}</CardContent>
      </Card>
    </section>
  );
}
