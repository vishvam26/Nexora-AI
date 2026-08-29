"use client";
import { Clock, Sparkles } from "lucide-react";

export default function ComingSoon({ title, desc }: { title: string; desc?: string }) {
  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div className="max-w-md w-full rounded-2xl border border-border bg-card p-8 text-center shadow-lg">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20">
          <Clock className="h-6 w-6 text-indigo-500" />
        </div>
        <h2 className="text-lg font-bold text-foreground flex items-center justify-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-500" /> {title}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {desc || "This feature is coming soon — currently Personal mode only. Team & Enterprise are reserved for future release."}
        </p>
        <div className="mt-4 inline-flex rounded-full bg-amber-500/10 border border-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-600">
          Coming Soon
        </div>
      </div>
    </div>
  );
}
