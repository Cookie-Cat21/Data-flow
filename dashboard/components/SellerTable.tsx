"use client";

import clsx from "clsx";
import type { SellerRow } from "../lib/types";

interface SellerTableProps {
  sellers: SellerRow[];
}

const tierBadge: Record<SellerRow["seller_tier"], string> = {
  top_seller: "bg-amber/10 text-amber border-amber/25",
  good_seller: "bg-teal/10 text-teal border-teal/25",
  standard: "bg-zinc-700/30 text-zinc-400 border-zinc-700",
  at_risk: "bg-red-500/10 text-red-400 border-red-500/25",
};

const tierLabel: Record<SellerRow["seller_tier"], string> = {
  top_seller: "Top",
  good_seller: "Good",
  standard: "Std",
  at_risk: "Risk",
};

export function SellerTable({ sellers }: SellerTableProps) {
  const top = sellers.slice(0, 10);

  return (
    <div className="bg-card border border-border rounded-sm p-6">
      <span className="font-mono text-[10px] tracking-widest uppercase text-zinc-500 block mb-5">
        Seller Leaderboard
      </span>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border">
              {["#", "Seller", "Location", "Revenue", "Orders", "Score", "SLA", "Tier"].map((h) => (
                <th
                  key={h}
                  className="font-mono text-[10px] tracking-widest uppercase text-zinc-600 pb-3 pr-4"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {top.map((row) => (
              <tr key={row.seller_id} className="border-b border-border/50 hover:bg-raised transition-colors">
                <td className="font-mono text-xs text-zinc-600 py-3 pr-4">{row.revenue_rank}</td>
                <td className="font-mono text-xs text-zinc-300 py-3 pr-4">
                  {row.seller_id.slice(0, 8)}…
                </td>
                <td className="font-mono text-xs text-zinc-500 py-3 pr-4">
                  {row.city}, {row.state}
                </td>
                <td className="font-mono text-xs text-amber font-bold py-3 pr-4">
                  ${(row.total_revenue / 1000).toFixed(1)}k
                </td>
                <td className="font-mono text-xs text-zinc-300 py-3 pr-4">{row.total_orders}</td>
                <td className="font-mono text-xs text-zinc-300 py-3 pr-4">
                  {row.avg_review_score?.toFixed(1) ?? "—"}
                </td>
                <td className="font-mono text-xs py-3 pr-4">
                  <span className={clsx(
                    "font-bold",
                    (row.on_time_rate ?? 0) >= 0.85 ? "text-teal" : "text-red-400"
                  )}>
                    {row.on_time_rate != null ? `${(row.on_time_rate * 100).toFixed(0)}%` : "—"}
                  </span>
                </td>
                <td className="py-3">
                  <span className={clsx(
                    "font-mono text-[10px] px-2 py-1 rounded-sm border",
                    tierBadge[row.seller_tier]
                  )}>
                    {tierLabel[row.seller_tier]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
