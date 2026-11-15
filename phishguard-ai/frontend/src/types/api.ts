/* ─── API response types matching the backend Pydantic schemas ─── */

export type ModelStatus = 'not_implemented' | 'implemented' | 'training' | 'trained' | 'error';
export type RiskLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical';
export type Modality = 'url' | 'email' | 'screenshot' | 'html' | 'multimodal';

/* Health */
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
}

/* Models */
export interface DetectionModelInfo {
  id: string;
  name: string;
  modality: Modality;
  status: ModelStatus;
  model_type: string | null;
  training_status: string | null;
  available: boolean;
  description: string;
}

export interface ModelsResponse {
  models: DetectionModelInfo[];
  total: number;
}

/* Statistics */
export interface RiskDistributionEntry {
  name: string;
  value: number;
  color: string;
}

export interface StatisticsResponse {
  total_scans: number;
  high_risk: number;
  suspicious: number;
  safe: number;
  models_available: number;
  risk_distribution: RiskDistributionEntry[];
  modality_usage?: Record<string, number>;
  recent_scans?: RecentScanSummary[];
}

export interface RecentScanSummary {
  id: string;
  scan_type: string;
  prediction: string;
  risk_score: number;
  target_summary: string | null;
  status: string;
  created_at: string;
}

/* Scans */
export interface ScanHistoryItem {
  id: string;
  scan_type: string;
  prediction: string;
  risk_score: number;
  target_summary: string | null;
  status: string;
  created_at: string;
}

export interface ScanHistoryResponse {
  scans: ScanHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ScanDetailResponse extends ScanHistoryItem {
  confidence: number | null;
  model_used: string | null;
  indicators: ScanIndicator[];
  explanation: string[];
  modality_results: Record<string, unknown> | null;
}

export interface ExplainableIndicator {
  indicator: string;
  source: string;
  impact: string;
  reason: string;
}

export interface ExplainResponse {
  explanation: ExplainableIndicator[];
}

export interface ScanRecord {
  id: string;
  input_type: Modality;
  target: string;
  risk_level: RiskLevel;
  timestamp: string;
  model_used: string | null;
  details: Record<string, unknown> | null;
}

export interface ScansResponse {
  scans: ScanRecord[];
  total: number;
}

/* Version */
export interface VersionResponse {
  name: string;
  version: string;
  environment: string;
}

/* ─── URL Scan (Section 2) ─── */

export interface URLScanRequest {
  url: string;
}

export interface URLScanResponse {
  scan_id?: string;
  url: string;
  prediction: string;
  confidence: number;
  risk_level: string;
  features: Record<string, number>;
  model: string;
}

/* ─── Multimodal Scan (Section 3: email, screenshot, HTML) ─── */

export interface ScanIndicator {
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

export interface MultimodalScanResponse {
  scan_id?: string;
  scan_type: string;
  prediction: string;
  risk_score: number;
  confidence: number | null;
  indicators: ScanIndicator[];
  explanation: string[];
  model: string;
  details?: Record<string, unknown>;
}

export interface MultimodalFusionRequest {
  url?: string | Record<string, unknown>;
  email?: Record<string, unknown>;
  screenshot?: Record<string, unknown>;
  html?: string | Record<string, unknown>;
}

export interface MultimodalFusionResponse {
  overall_risk_score: number;
  overall_prediction: string;
  modalities_analyzed: string[];
  modality_results: Record<string, unknown>;
  contributing_indicators: Array<Record<string, unknown>>;
  explanation: string[];
  fusion_weights?: Record<string, number>;
  confidence: number | null;
  model: string;
  scan_id?: string;
}

export interface EmailScanRequest {
  sender: string;
  subject: string;
  body: string;
  headers?: Record<string, string>;
}

export interface HTMLScanRequest {
  html: string;
}
