/**
 * WebSocket broadcast server.
 *
 * Polls the Gold Delta tables (via Databricks SQL or a local PostgreSQL mirror)
 * every 5 seconds and broadcasts a full DashboardPayload to all connected clients.
 *
 * Run: npm run ws-server
 */

import { WebSocketServer, WebSocket } from "ws";
import { Pool } from "pg";

const PORT = parseInt(process.env.WS_PORT ?? "8080", 10);
const POLL_INTERVAL_MS = 5_000;

const db = new Pool({ connectionString: process.env.DATABASE_URL });

const wss = new WebSocketServer({ port: PORT });
console.log(`[ws-server] Listening on ws://localhost:${PORT}`);

function broadcast(data: unknown) {
  const payload = JSON.stringify(data);
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });
}

// ── Query helpers ─────────────────────────────────────────────────────────

async function fetchKPI() {
  const { rows } = await db.query(`
    select
      coalesce(sum(case when purchase_date = current_date then payment_total end), 0)     as gmv_today,
      coalesce(count(case when purchase_date = current_date then 1 end), 0)               as orders_today,
      coalesce(avg(case when purchase_date = current_date then payment_total end), 0)     as avg_order_value,
      coalesce(avg(review_score), 0)                                                      as avg_review_score,
      coalesce(
        sum(case when delivered_on_time then 1 else 0 end)::float
          / nullif(count(case when order_status = 'delivered' then 1 end), 0), 0
      )                                                                                   as on_time_rate,
      count(case when order_status not in ('delivered','canceled','unavailable') then 1 end) as active_orders,
      now()                                                                               as updated_at
    from fct_orders
  `);
  return rows[0];
}

async function fetchGMVSeries() {
  const { rows } = await db.query(`
    select
      purchase_date::text as date,
      gmv,
      order_count,
      avg_order_value
    from rpt_gmv_daily
    order by purchase_date desc
    limit 90
  `);
  return rows.reverse();
}

async function fetchSellers() {
  const { rows } = await db.query(`
    select
      seller_id, city, state, seller_tier,
      total_orders, total_revenue, avg_review_score, on_time_rate, revenue_rank
    from rpt_seller_performance
    order by revenue_rank
    limit 20
  `);
  return rows;
}

async function fetchFunnel() {
  const { rows } = await db.query(`
    select
      order_status as status,
      count(*)     as count,
      round(count(*)::numeric / sum(count(*)) over () * 100, 1) as pct
    from fct_orders
    group by order_status
    order by count desc
  `);
  return rows;
}

// ── Poll loop ─────────────────────────────────────────────────────────────

async function poll() {
  try {
    const [kpi, gmv_series, sellers, funnel] = await Promise.all([
      fetchKPI(),
      fetchGMVSeries(),
      fetchSellers(),
      fetchFunnel(),
    ]);

    broadcast({ type: "snapshot", kpi, gmv_series, sellers, funnel });
  } catch (err) {
    console.error("[ws-server] Poll error:", err);
    broadcast({ type: "error", message: "Data fetch failed" });
  }
}

// Heartbeat to keep connections alive
setInterval(() => {
  broadcast({ type: "ping" });
}, 30_000);

// Main data poll
setInterval(poll, POLL_INTERVAL_MS);

// Initial push on first client connect
wss.on("connection", (socket) => {
  console.log("[ws-server] Client connected. Total:", wss.clients.size);
  poll(); // push immediately for new client
  socket.on("close", () =>
    console.log("[ws-server] Client disconnected. Total:", wss.clients.size)
  );
});

// Seed on startup
poll();
