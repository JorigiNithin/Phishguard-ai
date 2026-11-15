/**
 * Centralised API client for the PhishGuard AI backend.
 *
 * Uses the VITE_API_BASE_URL environment variable (defaults to "" which
 * lets the Vite dev-server proxy handle /api requests).
 */

import type {
  EmailScanRequest,
  ExplainResponse,
  HTMLScanRequest,
  HealthResponse,
  ModelsResponse,
  MultimodalFusionRequest,
  MultimodalFusionResponse,
  MultimodalScanResponse,
  ScanDetailResponse,
  ScanHistoryResponse,
  ScansResponse,
  StatisticsResponse,
  URLScanResponse,
  VersionResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

/* ─── helpers ───────────────────────────────────────────────────── */

async function request<T>(path: string, init?: RequestInit, retries = 1): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${BASE_URL}${path}`, init);
      if (!res.ok) {
        const body = await res.text().catch(() => '');
        let detail = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const parsed = JSON.parse(body);
          if (parsed.detail) detail = parsed.detail;
        } catch {
          // use default detail
        }
        throw new Error(detail);
      }
      return (await res.json()) as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
  }

  throw lastError!;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function postFormData<T>(path: string, formData: FormData): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: formData,
  });
}

/* ─── public API ────────────────────────────────────────────────── */

export const api = {
  /* ── System ── */

  /** Check backend health / connectivity. */
  getHealth: () => request<HealthResponse>('/api/health'),

  /** Fetch detection model statuses. */
  getModels: () => request<ModelsResponse>('/api/models'),

  /** Fetch aggregated scan statistics. */
  getStatistics: () => request<StatisticsResponse>('/api/statistics'),

  /** Fetch dashboard stats from persisted scan history. */
  getDashboardStatistics: () => request<StatisticsResponse>('/api/dashboard/statistics'),

  /** Fetch scan history. */
  getScans: () => request<ScansResponse>('/api/scans'),

  /** Fetch paginated scan history for the History page. */
  getScanHistory: (params?: { scan_type?: string; prediction?: string; search?: string; page?: number; page_size?: number; }) => {
    const query = new URLSearchParams();
    if (params?.scan_type) query.set('scan_type', params.scan_type);
    if (params?.prediction) query.set('prediction', params.prediction);
    if (params?.search) query.set('search', params.search);
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    return request<ScanHistoryResponse>(`/api/scans/history${query.toString() ? `?${query.toString()}` : ''}`);
  },

  /** Fetch a single saved scan by id. */
  getScanDetail: (scanId: string) => request<ScanDetailResponse>(`/api/scans/${scanId}`),

  /** Fetch structured explainability breakdown for a scan. */
  getScanExplanation: (scanId: string) => request<ExplainResponse>(`/api/scans/${scanId}/explain`),

  /** Delete a saved scan by id. */
  deleteScan: (scanId: string) => request<{ detail: string; id: string }>(`/api/scans/${scanId}`, { method: 'DELETE' }),

  /** Fetch application version info. */
  getVersion: () => request<VersionResponse>('/api/version'),

  /* ── URL Scan (Section 2) ── */

  /** Analyse a URL for phishing indicators. */
  scanUrl: (url: string) =>
    postJson<URLScanResponse>('/api/scans/url', { url }),

  /* ── Email Scan (Section 3) ── */

  /** Analyse email content for phishing indicators. */
  scanEmail: (data: EmailScanRequest) =>
    postJson<MultimodalScanResponse>('/api/scans/email', data),

  /* ── Screenshot Scan (Section 3) ── */

  /** Upload and analyse a screenshot for phishing indicators. */
  scanScreenshot: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return postFormData<MultimodalScanResponse>('/api/scans/screenshot', formData);
  },

  /* ── HTML Scan (Section 3) ── */

  /** Analyse raw HTML source for phishing indicators. */
  scanHtml: (html: string) =>
    postJson<MultimodalScanResponse>('/api/scans/html', { html }),

  /** Fuse multiple modalities into a single risk assessment. */
  scanMultimodal: (data: MultimodalFusionRequest) =>
    postJson<MultimodalFusionResponse>('/api/scans/multimodal', data),
};
