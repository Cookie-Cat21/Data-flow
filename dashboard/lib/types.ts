export interface KPISnapshot {
  gmv_today: number;
  orders_today: number;
  avg_order_value: number;
  avg_review_score: number;
  on_time_rate: number;
  active_orders: number;
  updated_at: string;
}

export interface GMVDataPoint {
  date: string;
  gmv: number;
  order_count: number;
  avg_order_value: number;
}

export interface SellerRow {
  seller_id: string;
  city: string;
  state: string;
  seller_tier: "top_seller" | "good_seller" | "standard" | "at_risk";
  total_orders: number;
  total_revenue: number;
  avg_review_score: number;
  on_time_rate: number;
  revenue_rank: number;
}

export interface OrderFunnelRow {
  status: string;
  count: number;
  pct: number;
}

export interface DashboardPayload {
  type: "snapshot";
  kpi: KPISnapshot;
  gmv_series: GMVDataPoint[];
  sellers: SellerRow[];
  funnel: OrderFunnelRow[];
}

export type WSMessage = DashboardPayload | { type: "ping" } | { type: "error"; message: string };
