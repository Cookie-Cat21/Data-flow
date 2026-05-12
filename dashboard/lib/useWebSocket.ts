"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WSMessage } from "./types";

type Status = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status, setStatus] = useState<Status>("connecting");
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const socket = new WebSocket(url);

    socket.onopen = () => setStatus("connected");

    socket.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        if (msg.type !== "ping") setLastMessage(msg);
      } catch {
        // ignore malformed frames
      }
    };

    socket.onerror = () => setStatus("error");

    socket.onclose = () => {
      setStatus("disconnected");
      // exponential back-off reconnect
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.current = socket;
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      reconnectTimer.current && clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  return { status, lastMessage };
}
