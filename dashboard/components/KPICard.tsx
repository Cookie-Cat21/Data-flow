"use client";

import clsx from "clsx";

interface KPICardProps {
  label: string;
  value: string | number;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  accent?: "amber" | "teal" | "default";
}

export function KPICard({ label, value, sub, trend, accent = "default" }: KPICardProps) {
  const accentColor = {
    amber: "text-amber",
    teal: "text-teal",
    default: "text-white",
  }[accent];

  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : null;
  const trendColor = trend === "up" ? "text-teal" : trend === "down" ? "text-red-400" : "";

  return (
    <div className="bg-card border border-border rounded-sm p-6 flex flex-col gap-2 hover:bg-raised transition-colors">
      <span className="font-mono text-[10px] tracking-widest uppercase text-zinc-500">{label}</span>
      <span className={clsx("font-serif text-4xl font-black leading-none", accentColor)}>
        {value}
        {trendIcon && (
          <span className={clsx("font-mono text-base ml-2", trendColor)}>{trendIcon}</span>
        )}
      </span>
      {sub && <span className="font-mono text-xs text-zinc-500">{sub}</span>}
    </div>
  );
}
