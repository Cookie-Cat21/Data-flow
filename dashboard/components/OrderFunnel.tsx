"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import type { OrderFunnelRow } from "../lib/types";

interface OrderFunnelProps {
  data: OrderFunnelRow[];
}

const STATUS_COLORS: Record<string, string> = {
  created: "#60a5fa",
  approved: "#818cf8",
  invoiced: "#a78bfa",
  processing: "#f5a623",
  shipped: "#00d4aa",
  delivered: "#34d399",
  canceled: "#f87171",
  unavailable: "#6b7280",
};

export function OrderFunnel({ data }: OrderFunnelProps) {
  return (
    <div className="bg-card border border-border rounded-sm p-6">
      <span className="font-mono text-[10px] tracking-widest uppercase text-zinc-500 block mb-5">
        Order Status Funnel
      </span>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 48, left: 0, bottom: 0 }}>
          <XAxis
            type="number"
            tick={{ fill: "#52525b", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="status"
            tick={{ fill: "#a1a1aa", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
            width={80}
          />
          <Tooltip
            contentStyle={{
              background: "#18181d",
              border: "1px solid #252530",
              borderRadius: "2px",
              fontFamily: "JetBrains Mono",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#a1a1aa" }}
            itemStyle={{ color: "#f5a623" }}
          />
          <Bar dataKey="count" radius={[0, 2, 2, 0]}>
            {data.map((entry) => (
              <Cell key={entry.status} fill={STATUS_COLORS[entry.status] ?? "#52525b"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
