"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { GMVDataPoint } from "../lib/types";

interface GMVChartProps {
  data: GMVDataPoint[];
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-raised border border-border rounded-sm p-3">
      <p className="font-mono text-xs text-zinc-400 mb-1">
        {label ? format(parseISO(label), "MMM d, yyyy") : ""}
      </p>
      <p className="font-mono text-sm text-amber font-bold">
        {formatCurrency(payload[0]?.value ?? 0)}
      </p>
      <p className="font-mono text-xs text-zinc-500">
        {payload[1]?.value ?? 0} orders
      </p>
    </div>
  );
}

export function GMVChart({ data }: GMVChartProps) {
  return (
    <div className="bg-card border border-border rounded-sm p-6">
      <div className="flex items-baseline gap-3 mb-6">
        <span className="font-mono text-[10px] tracking-widest uppercase text-zinc-500">
          GMV Over Time
        </span>
        <span className="font-mono text-xs text-teal">{data.length} days</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gmvGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f5a623" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f5a623" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#252530" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => format(parseISO(d), "MMM d")}
            tick={{ fill: "#52525b", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: "#52525b", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
            width={64}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="gmv"
            stroke="#f5a623"
            strokeWidth={2}
            fill="url(#gmvGrad)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
