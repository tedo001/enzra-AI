"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FrameResult } from "@/lib/types";
import { WS_URL } from "@/lib/api";

interface StreamState {
  frame: FrameResult | null;
  connected: boolean;
  lastVoice: string | null;
}

/**
 * Subscribes to the backend WebSocket and exposes the latest FrameResult.
 * Auto-reconnects with backoff and speaks voice alerts via the Web Speech API.
 */
export function useRailVisionStream(enabled = true): StreamState {
  const [frame, setFrame] = useState<FrameResult | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastVoice, setLastVoice] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.05;
    u.pitch = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let closed = false;

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryRef.current = 0;
      };
      ws.onmessage = (evt) => {
        const data: FrameResult = JSON.parse(evt.data);
        setFrame(data);
        if (data.voice_alert) {
          setLastVoice(data.voice_alert);
          speak(data.voice_alert);
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (closed) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 8000);
        retryRef.current += 1;
        setTimeout(connect, delay);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closed = true;
      wsRef.current?.close();
    };
  }, [enabled, speak]);

  return { frame, connected, lastVoice };
}
