"use client";

import { useEffect, useState } from "react";
import { useWebSocket } from "../../lib/useWebSocket";
import { KPICard } from "../../components/KPICard";
import { GMVChart } from "../../components/GMVChart";
import { SellerTable } from "../../components/SellerTable";
import { OrderFunnel } from "../../components/OrderFunnel";
import { LiveIndicator } from "../../components/LiveIndicator";
import type { DashboardPayload, KPISnapshot, GMVDataPoint, SellerRow, OrderFunnelRow } from "../../lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8080";

function fmt(n: number, style: "currency" | "number" | "percent" = "number", compact = false) {
  const opts: Intl.NumberFormatOptions = {
    style,
    currency: "USD",
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: style === "percent" ? 1 : compact ? 1 : 0,
  };
  if (style !== "currency") delete opts.currency;
  if (style === "percent") return `${(n * 100).toFixed(1)}%`;
  return new Intl.NumberFormat("en-US", opts).format(n);
}

export default function DashboardPage() {
  const { status, lastMessage } = useWebSocket(WS_URL);
  const [kpi, setKpi] = useState<KPISnapshot | null>(null);
  const [gmvSeries, setGmvSeries] = useState<GMVDataPoint[]>([]);
  const [sellers, setSellers] = useState<SellerRow[]>([]);
  const [funnel, setFunnel] = useState<OrderFunnelRow[]>([]);

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== "snapshot") return;
    const p = lastMessage as DashboardPayload;
    setKpi(p.kpi);
    setGmvSeries(p.gmv_series);
    setSellers(p.sellers);
    setFunnel(p.funnel);
  }, [lastMessage]);

  return (
    <div className="min-h-screen bg-bg text-white" style={{ fontFamily: "DM Sans, sans-serif" }}>
      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <header className="flex items-end justify-between mb-8 pb-6 border-b border-border">
          <div>
            <p className="font-mono text-[10px] tracking-widest uppercase text-amber mb-1">
              Real-time Analytics Pipeline
            </p>
            <h1 className="font-serif text-4xl font-black text-white leading-none">
              Data<span className="italic text-amber">Flow</span>
            </h1>
          </div>
          <LiveIndicator status={status} updatedAt={kpi?.updated_at} />
        </header>

        {/* KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-border border border-border rounded-sm overflow-hidden mb-4">
          <KPICard
            label="GMV Today"
            value={kpi ? fmt(kpi.gmv_today, "currency", true) : "—"}
            accent="amber"
          />
          <KPICard
            label="Orders Today"
            value={kpi ? fmt(kpi.orders_today) : "—"}
            accent="default"
          />
          <KPICard
            label="Avg Order"
            value={kpi ? fmt(kpi.avg_order_value, "currency") : "—"}
            accent="default"
          />
          <KPICard
            label="Avg Review"
            value={kpi ? `${kpi.avg_review_score.toFixed(2)} ★` : "—"}
            accent="teal"
          />
          <KPICard
            label="On-Time Rate"
            value={kpi ? fmt(kpi.on_time_rate, "percent") : "—"}
            accent={kpi && kpi.on_time_rate >= 0.85 ? "teal" : "default"}
          />
          <KPICard
            label="Active Orders"
            value={kpi ? fmt(kpi.active_orders) : "—"}
            accent="default"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          <div className="lg:col-span-2">
            <GMVChart data={gmvSeries} />
          </div>
          <OrderFunnel data={funnel} />
        </div>

        {/* Seller Table */}
        <SellerTable sellers={sellers} />

        {/* Footer */}
        <footer className="mt-8 pt-6 border-t border-border flex items-center justify-between">
          <span className="font-mono text-xs text-zinc-600">
            DataFlow · Kafka · Spark · dbt · Airflow
          </span>
          <span className="font-mono text-xs text-zinc-600">
            Dataset: Olist Brazilian E-Commerce
          </span>
        </footer>
      </div>
    </div>
  );
}
