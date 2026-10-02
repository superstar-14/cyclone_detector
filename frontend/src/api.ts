/**
 * IMD Cyclone Detector – API Client
 */
// In production or when hosted together, default to relative path '' so requests go to current origin.
// In dev mode, fall back to 'http://localhost:8000' if VITE_API_URL is not set.
const API_BASE = import.meta.env.VITE_API_URL !== undefined
  ? import.meta.env.VITE_API_URL
  : (import.meta.env.PROD ? '' : 'http://localhost:8000');

function getWsUrl(): string {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  if (typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/ws/live`;
  }
  return 'ws://localhost:8000/ws/live';
}

const WS_URL = getWsUrl();

import type { Storm, Forecast, DistrictImpact, DataSourceHealth, ForecastPoint } from './types';

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

async function postJSON<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  // Storms
  getActiveStorms: () => fetchJSON<Storm[]>('/api/storms/active'),
  getStorm: (id: string) => fetchJSON<Storm>(`/api/storms/${id}`),
  getStormEye: (id: string) => fetchJSON<any>(`/api/storms/${id}/eye`),
  getStormForecast: (id: string) => fetchJSON<Forecast>(`/api/storms/${id}/forecast`),
  getForecastTable: (id: string, leads = '0,6,12,18,24,36,48,60,72') =>
    fetchJSON<{ storm_id: string; points: ForecastPoint[] }>(`/api/storms/${id}/forecast-table?leads=${leads}`),
  getImpactSwath: (id: string) => fetchJSON<any>(`/api/storms/${id}/impact/swath`),
  getDistrictImpacts: (id: string) => fetchJSON<DistrictImpact[]>(`/api/storms/${id}/impact/districts`),

  // Alerts & SMS Automation
  sendAlertSMS: (payload: {
    district_name: string;
    state: string;
    vulnerability_score: number;
    wind_speed_kmh: number;
    rainfall_mm?: number;
    eta?: string;
    language?: string;
    provider?: string;
  }) => postJSON<any>('/api/alerts/send-sms', payload),

  evaluateAndTriggerThreshold: (payload: {
    storm_id: string;
    threshold?: number;
    language?: string;
    districts: any[];
  }) => postJSON<any>('/api/alerts/evaluate-and-trigger', payload),

  getAlertHistory: () => fetchJSON<any>('/api/alerts/history'),
  getAlertTemplates: () => fetchJSON<any>('/api/alerts/templates'),

  // Layers
  getLayers: () => fetchJSON<{ layers: any[] }>('/api/layers/'),
  getLayerData: (name: string, time?: string) =>
    fetchJSON<any>(`/api/layers/${name}${time ? `?time=${time}` : ''}`),

  // History
  getHistoricalCyclones: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchJSON<any>(`/api/history/cyclones${qs}`);
  },
  getAnalogs: (stormId: string) => fetchJSON<any>(`/api/history/analogs?storm_id=${stormId}`),
  getSeasonality: () => fetchJSON<any>('/api/history/seasonality'),

  // Health
  getSourceHealth: () => fetchJSON<{ sources: DataSourceHealth[] }>('/api/health/sources'),
  getSystemHealth: () => fetchJSON<any>('/api/health/system'),

  // Config
  getConfig: () => fetchJSON<any>('/api/config'),
};

// ── WebSocket ──────────────────────────────────────────────

export type WSMessage = {
  type: 'storm_update' | 'forecast_update' | 'alert' | 'data_status' | 'heartbeat' | 'connection';
  data?: any;
  message?: string;
  timestamp?: number;
};

export function connectWebSocket(
  onMessage: (msg: WSMessage) => void,
  onError?: (err: Event) => void,
): WebSocket {
  const ws = new WebSocket(WS_URL);

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WSMessage;
      onMessage(msg);
    } catch (e) {
      console.warn('Failed to parse WS message:', event.data);
    }
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
    onError?.(err);
  };

  ws.onclose = () => {
    console.info('WebSocket closed, reconnecting in 5s...');
    setTimeout(() => connectWebSocket(onMessage, onError), 5000);
  };

  return ws;
}
