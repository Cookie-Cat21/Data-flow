"use client";

import clsx from "clsx";

interface LiveIndicatorProps {
  status: "connecting" | "connected" | "disconnected" | "error";
  updatedAt?: string;
}

export function LiveIndicator({ status, updatedAt }: LiveIndicatorProps) {
  const label = {
    connecting: "Connecting...",
    connected: "Live",
    disconnected: "Reconnecting...",
    error: "Error",
  }[status];

  const color = {
    connecting: "bg-zinc-500",
    connected: "bg-teal",
    disconnected: "bg-amber",
    error: "bg-red-400",
  }[status];

  return (
    <div className="flex items-center gap-2">
      <span className={clsx("w-2 h-2 rounded-full", color, status === "connected" && "animate-pulse")} />
      <span className="font-mono text-xs text-zinc-500">{label}</span>
      {updatedAt && status === "connected" && (
        <span className="font-mono text-xs text-zinc-600">
          · {new Date(updatedAt).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
