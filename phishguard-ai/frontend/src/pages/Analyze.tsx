import { useState, useRef, type FormEvent } from 'react';
import {
  Link,
  Mail,
  Image,
  Code2,
  AlertCircle,
  Upload,
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  URLScanResponse,
  MultimodalScanResponse,
  MultimodalFusionResponse,
  ScanIndicator,
} from '../types/api';

type Tab = 'url' | 'email' | 'screenshot' | 'html' | 'multimodal';

type ScanResult =
  | { type: 'url'; data: URLScanResponse }
  | { type: 'multimodal'; data: MultimodalScanResponse }
  | { type: 'fusion'; data: MultimodalFusionResponse };

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'url', label: 'URL', icon: <Link className="h-4 w-4" /> },
  { id: 'email', label: 'Email', icon: <Mail className="h-4 w-4" /> },
  { id: 'screenshot', label: 'Screenshot', icon: <Image className="h-4 w-4" /> },
  { id: 'html', label: 'HTML', icon: <Code2 className="h-4 w-4" /> },
  { id: 'multimodal', label: 'Fusion', icon: <Layers className="h-4 w-4" /> },
];

export default function Analyze() {
  const [tab, setTab] = useState<Tab>('url');

  // Form state
  const [url, setUrl] = useState('');
  const [emailSender, setEmailSender] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [htmlContent, setHtmlContent] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // UI state
  const [validationError, setValidationError] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ScanResult | null>(null);

  const resetState = () => {
    setValidationError('');
    setError('');
    setResult(null);
  };

  const switchTab = (t: Tab) => {
    setTab(t);
    setFile(null);
    setFilePreview(null);
    resetState();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    resetState();

    // Preview for screenshots
    if (selected && selected.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => setFilePreview(reader.result as string);
      reader.readAsDataURL(selected);
    } else {
      setFilePreview(null);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError('');
    setError('');
    setResult(null);

    // --- Validation ---
    if (tab === 'url') {
      try {
        new URL(url);
      } catch {
        setValidationError('Please enter a valid URL (e.g. https://example.com)');
        return;
      }
    }
    if (tab === 'email') {
      if (!emailSender.trim() || !emailSender.includes('@')) {
        setValidationError('Please enter a valid sender email address.');
        return;
      }
      if (!emailBody.trim()) {
        setValidationError('Please enter the email body content.');
        return;
      }
    }
    if (tab === 'screenshot') {
      if (!file) {
        setValidationError('Please select a screenshot file.');
        return;
      }
      const allowed = ['image/png', 'image/jpeg', 'image/jpg'];
      if (!allowed.includes(file.type)) {
        setValidationError('Only PNG and JPEG files are accepted.');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setValidationError('File size must be under 10 MB.');
        return;
      }
    }
    if (tab === 'html') {
      if (!htmlContent.trim()) {
        setValidationError('Please enter HTML source code to analyse.');
        return;
      }
      if (htmlContent.length > 500_000) {
        setValidationError('HTML content exceeds the 500 KB limit.');
        return;
      }
    }
    if (tab === 'multimodal') {
      const hasUrl = Boolean(url.trim());
      const hasEmail = Boolean(emailSender.trim() || emailSubject.trim() || emailBody.trim());
      const hasHtml = Boolean(htmlContent.trim());

      if (!hasUrl && !hasEmail && !hasHtml) {
        setValidationError('Please provide at least one input (URL, Email, or HTML) for multimodal fusion.');
        return;
      }
      if (hasUrl) {
        try {
          new URL(url);
        } catch {
          setValidationError('Please enter a valid URL (e.g. https://example.com)');
          return;
        }
      }
      if (hasEmail && (!emailSender.includes('@') || !emailBody.trim())) {
        setValidationError('For email analysis, a valid sender address and email body are required.');
        return;
      }
    }

    // --- Call API ---
    setLoading(true);
    try {
      if (tab === 'url') {
        const data = await api.scanUrl(url);
        setResult({ type: 'url', data });
      } else if (tab === 'email') {
        const data = await api.scanEmail({
          sender: emailSender.trim(),
          subject: emailSubject.trim(),
          body: emailBody,
        });
        setResult({ type: 'multimodal', data });
      } else if (tab === 'screenshot') {
        const data = await api.scanScreenshot(file!);
        setResult({ type: 'multimodal', data });
      } else if (tab === 'html') {
        const data = await api.scanHtml(htmlContent);
        setResult({ type: 'multimodal', data });
      } else if (tab === 'multimodal') {
        const payload: Record<string, unknown> = {};
        if (url.trim()) payload.url = url.trim();
        if (emailBody.trim()) {
          payload.email = {
            sender: emailSender.trim(),
            subject: emailSubject.trim(),
            body: emailBody,
          };
        }
        if (htmlContent.trim()) payload.html = htmlContent;
        const data = await api.scanMultimodal(payload);
        setResult({ type: 'fusion', data });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed. Check backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analyze</h1>
        <p className="text-sm text-gray-400 mt-1">
          Submit a URL, email, screenshot, or HTML for phishing analysis
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-navy-900 border border-navy-800 rounded-lg p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => switchTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id
                ? 'bg-navy-800 text-teal-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.icon}
            <span className="hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-navy-900 border border-navy-800 rounded-xl p-6 space-y-5"
      >
        {/* URL Tab */}
        {tab === 'url' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              URL to analyse
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); resetState(); }}
              placeholder="https://example.com"
              className="w-full px-4 py-2.5 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
            />
          </div>
        )}

        {/* Email Tab */}
        {tab === 'email' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Sender email address
              </label>
              <input
                type="text"
                value={emailSender}
                onChange={(e) => { setEmailSender(e.target.value); resetState(); }}
                placeholder="sender@example.com"
                className="w-full px-4 py-2.5 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={emailSubject}
                onChange={(e) => { setEmailSubject(e.target.value); resetState(); }}
                placeholder="Email subject line"
                className="w-full px-4 py-2.5 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email body
              </label>
              <textarea
                value={emailBody}
                onChange={(e) => { setEmailBody(e.target.value); resetState(); }}
                rows={8}
                placeholder="Paste the full email content here…"
                className="w-full px-4 py-2.5 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50 resize-y"
              />
            </div>
          </div>
        )}

        {/* Screenshot Tab */}
        {tab === 'screenshot' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Upload screenshot (PNG, JPEG — max 10 MB)
            </label>
            <div
              onClick={() => fileRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 py-10 border-2 border-dashed border-navy-700 rounded-lg cursor-pointer hover:border-teal-600/50 transition-colors"
            >
              {filePreview ? (
                <img
                  src={filePreview}
                  alt="Preview"
                  className="max-h-48 max-w-full rounded-md object-contain"
                />
              ) : (
                <Upload className="h-8 w-8 text-gray-500" />
              )}
              <span className="text-sm text-gray-400">
                {file ? file.name : 'Click to select a file'}
              </span>
              {file && (
                <span className="text-xs text-gray-500">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* HTML Tab */}
        {tab === 'html' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              HTML source code
            </label>
            <textarea
              value={htmlContent}
              onChange={(e) => { setHtmlContent(e.target.value); resetState(); }}
              rows={12}
              placeholder="<html>&#10;  <head><title>Example</title></head>&#10;  <body>Paste HTML source here…</body>&#10;</html>"
              className="w-full px-4 py-2.5 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-teal-500/50 resize-y"
            />
            <p className="text-xs text-gray-500 mt-1">
              Max 500 KB. HTML is analysed statically — never executed.
            </p>
          </div>
        )}

        {/* Multimodal Fusion Tab */}
        {tab === 'multimodal' && (
          <div className="space-y-4">
            <div className="p-3 bg-navy-800/80 border border-teal-800/40 rounded-lg text-xs text-teal-300">
              Multimodal Fusion combines lexical URL analysis, email heuristic inspection, and static HTML parsing into a single unified risk score using configurable evidence weights. Provide any combination of inputs.
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                URL (optional)
              </label>
              <input
                type="text"
                value={url}
                onChange={(e) => { setUrl(e.target.value); resetState(); }}
                placeholder="https://example.com/login"
                className="w-full px-4 py-2 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email Sender (optional)
                </label>
                <input
                  type="text"
                  value={emailSender}
                  onChange={(e) => { setEmailSender(e.target.value); resetState(); }}
                  placeholder="alerts@bank.com"
                  className="w-full px-4 py-2 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email Subject (optional)
                </label>
                <input
                  type="text"
                  value={emailSubject}
                  onChange={(e) => { setEmailSubject(e.target.value); resetState(); }}
                  placeholder="Urgent account alert"
                  className="w-full px-4 py-2 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Email Body (optional)
              </label>
              <textarea
                value={emailBody}
                onChange={(e) => { setEmailBody(e.target.value); resetState(); }}
                rows={4}
                placeholder="Paste email body text here…"
                className="w-full px-4 py-2 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50 resize-y"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                HTML Source Code (optional)
              </label>
              <textarea
                value={htmlContent}
                onChange={(e) => { setHtmlContent(e.target.value); resetState(); }}
                rows={4}
                placeholder="<html>...</html>"
                className="w-full px-4 py-2 rounded-lg bg-navy-800 border border-navy-700 text-gray-100 placeholder-gray-500 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-teal-500/50 resize-y"
              />
            </div>
          </div>
        )}

        {/* Validation error */}
        {validationError && (
          <div className="flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {validationError}
          </div>
        )}

        {/* API error */}
        {error && (
          <div className="flex items-start gap-3 bg-red-900/20 border border-red-800/40 text-red-300 rounded-lg px-4 py-3 text-sm">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Analysis failed</p>
              <p className="text-xs text-red-400 mt-1">{error}</p>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-teal-600 hover:bg-teal-500 disabled:bg-teal-800 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analysing…
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {result.type === 'url' ? (
            <URLResultCard data={result.data} />
          ) : result.type === 'fusion' ? (
            <FusionResultCard data={result.data} />
          ) : (
            <MultimodalResultCard data={result.data} />
          )}
        </div>
      )}
    </div>
  );
}

/* ─── URL Result Card ─── */

function URLResultCard({ data }: { data: URLScanResponse }) {
  const [showFeatures, setShowFeatures] = useState(false);
  const isPhishing = data.prediction === 'phishing';

  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div
        className={`px-6 py-4 border-b ${
          isPhishing
            ? 'border-red-800/40 bg-red-900/10'
            : 'border-emerald-800/40 bg-emerald-900/10'
        }`}
      >
        <div className="flex items-center gap-3">
          {isPhishing ? (
            <ShieldAlert className="h-6 w-6 text-red-400" />
          ) : (
            <ShieldCheck className="h-6 w-6 text-emerald-400" />
          )}
          <div>
            <h3 className="font-semibold text-lg">
              {isPhishing ? 'Phishing Detected' : 'Legitimate URL'}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Model: {data.model} • Risk level: {data.risk_level}
            </p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-sm text-gray-400">Confidence</p>
            <p className={`text-xl font-bold ${isPhishing ? 'text-red-400' : 'text-emerald-400'}`}>
              {(data.confidence * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* URL */}
      <div className="px-6 py-3 border-b border-navy-800">
        <p className="text-xs text-gray-500 mb-1">Analysed URL</p>
        <p className="text-sm text-gray-300 font-mono break-all">{data.url}</p>
      </div>

      {/* Confidence bar */}
      <div className="px-6 py-3 border-b border-navy-800">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Risk</span>
          <span>{data.risk_level}</span>
        </div>
        <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              isPhishing ? 'bg-red-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${data.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Features toggle */}
      <div className="px-6 py-3">
        <button
          onClick={() => setShowFeatures(!showFeatures)}
          className="flex items-center gap-2 text-sm text-teal-400 hover:text-teal-300 transition-colors"
        >
          {showFeatures ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          {showFeatures ? 'Hide' : 'Show'} extracted features ({Object.keys(data.features).length})
        </button>
        {showFeatures && (
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
            {Object.entries(data.features).map(([key, val]) => (
              <div key={key} className="bg-navy-800 rounded-lg px-3 py-2">
                <p className="text-xs text-gray-500">{key.replace(/_/g, ' ')}</p>
                <p className="text-sm font-medium text-gray-300">
                  {typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(4)) : String(val)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Multimodal Result Card (email, screenshot, HTML) ─── */

function MultimodalResultCard({ data }: { data: MultimodalScanResponse }) {
  const [showDetails, setShowDetails] = useState(false);

  const predictionConfig = {
    phishing: { icon: ShieldAlert, color: 'red', label: 'Phishing Detected' },
    suspicious: { icon: AlertTriangle, color: 'amber', label: 'Suspicious Content' },
    safe: { icon: ShieldCheck, color: 'emerald', label: 'No Threats Detected' },
  }[data.prediction] ?? { icon: Shield, color: 'gray', label: data.prediction };

  const PredIcon = predictionConfig.icon;
  const c = predictionConfig.color;

  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className={`px-6 py-4 border-b border-${c}-800/40 bg-${c}-900/10`}>
        <div className="flex items-center gap-3">
          <PredIcon className={`h-6 w-6 text-${c}-400`} />
          <div>
            <h3 className="font-semibold text-lg">{predictionConfig.label}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Scan type: {data.scan_type} • Model: {data.model}
            </p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-sm text-gray-400">Risk score</p>
            <p className={`text-xl font-bold text-${c}-400`}>{data.risk_score}/100</p>
          </div>
        </div>
      </div>

      {/* Risk bar */}
      <div className="px-6 py-3 border-b border-navy-800">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Risk level</span>
          <span>{data.risk_score}/100</span>
        </div>
        <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              data.risk_score >= 60
                ? 'bg-red-500'
                : data.risk_score >= 30
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
            }`}
            style={{ width: `${data.risk_score}%` }}
          />
        </div>
      </div>

      {/* Indicators */}
      {data.indicators.length > 0 && (
        <div className="px-6 py-4 border-b border-navy-800">
          <h4 className="text-sm font-medium text-gray-300 mb-3">
            Detected Indicators ({data.indicators.length})
          </h4>
          <div className="space-y-2">
            {data.indicators.map((ind, i) => (
              <IndicatorRow key={i} indicator={ind} />
            ))}
          </div>
        </div>
      )}

      {/* Explanation */}
      {data.explanation.length > 0 && (
        <div className="px-6 py-4 border-b border-navy-800">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Analysis Summary</h4>
          <ul className="space-y-1">
            {data.explanation.map((line, i) => (
              <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                <span className="text-teal-500 mt-1">•</span>
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Details toggle */}
      {data.details && Object.keys(data.details).length > 0 && (
        <div className="px-6 py-3">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-2 text-sm text-teal-400 hover:text-teal-300 transition-colors"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide' : 'Show'} additional details
          </button>
          {showDetails && (
            <div className="mt-3 bg-navy-800 rounded-lg p-4">
              <pre className="text-xs text-gray-400 whitespace-pre-wrap break-all">
                {JSON.stringify(data.details, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Indicator Row ─── */

function IndicatorRow({ indicator }: { indicator: ScanIndicator }) {
  const severityStyles = {
    high: 'bg-red-900/30 border-red-800/40 text-red-300',
    medium: 'bg-amber-900/30 border-amber-800/40 text-amber-300',
    low: 'bg-blue-900/30 border-blue-800/40 text-blue-300',
  }[indicator.severity] ?? 'bg-gray-900/30 border-gray-800/40 text-gray-300';

  const badgeStyles = {
    high: 'bg-red-800/50 text-red-300',
    medium: 'bg-amber-800/50 text-amber-300',
    low: 'bg-blue-800/50 text-blue-300',
  }[indicator.severity] ?? 'bg-gray-800/50 text-gray-300';

  return (
    <div className={`flex items-start gap-3 rounded-lg border px-3 py-2 text-sm ${severityStyles}`}>
      <span className={`shrink-0 mt-0.5 text-xs font-medium px-2 py-0.5 rounded ${badgeStyles}`}>
        {indicator.severity.toUpperCase()}
      </span>
      <div>
        <p className="font-medium">{indicator.name.replace(/_/g, ' ')}</p>
        <p className="text-xs opacity-80 mt-0.5">{indicator.description}</p>
      </div>
    </div>
  );
}

/* ─── Multimodal Fusion Result Card ─── */

function FusionResultCard({ data }: { data: MultimodalFusionResponse }) {
  const [showModalityResults, setShowModalityResults] = useState(false);

  const predictionConfig = {
    phishing: { icon: ShieldAlert, color: 'red', label: 'Phishing Detected' },
    suspicious: { icon: AlertTriangle, color: 'amber', label: 'Suspicious Content' },
    safe: { icon: ShieldCheck, color: 'emerald', label: 'No Threats Detected' },
  }[data.overall_prediction] ?? { icon: Shield, color: 'gray', label: data.overall_prediction };

  const PredIcon = predictionConfig.icon;
  const c = predictionConfig.color;

  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className={`px-6 py-4 border-b border-${c}-800/40 bg-${c}-900/10`}>
        <div className="flex items-center gap-3">
          <PredIcon className={`h-6 w-6 text-${c}-400`} />
          <div>
            <h3 className="font-semibold text-lg">{predictionConfig.label}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Multimodal Fusion Engine • {data.modalities_analyzed.length} modalities analyzed
              {data.scan_id && ` • ID: ${data.scan_id.slice(0, 8)}`}
            </p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-sm text-gray-400">Overall Risk</p>
            <p className={`text-xl font-bold text-${c}-400`}>{data.overall_risk_score}/100</p>
          </div>
        </div>
      </div>

      {/* Risk bar */}
      <div className="px-6 py-3 border-b border-navy-800">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Overall Risk Score</span>
          <span>{data.overall_risk_score}/100</span>
        </div>
        <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              data.overall_risk_score >= 60
                ? 'bg-red-500'
                : data.overall_risk_score >= 30
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
            }`}
            style={{ width: `${data.overall_risk_score}%` }}
          />
        </div>
      </div>

      {/* Modalities analyzed pills */}
      <div className="px-6 py-3 border-b border-navy-800 flex flex-wrap items-center gap-2">
        <span className="text-xs text-gray-400">Analyzed modalities:</span>
        {data.modalities_analyzed.map((m) => (
          <span key={m} className="px-2.5 py-0.5 rounded-full text-xs font-medium uppercase bg-teal-950 border border-teal-800 text-teal-300">
            {m}
          </span>
        ))}
      </div>

      {/* Contributing Indicators */}
      {data.contributing_indicators.length > 0 && (
        <div className="px-6 py-4 border-b border-navy-800">
          <h4 className="text-sm font-medium text-gray-300 mb-3">
            Contributing Indicators ({data.contributing_indicators.length})
          </h4>
          <div className="space-y-2">
            {data.contributing_indicators.map((ind, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg border border-navy-700 bg-navy-800/60 px-3 py-2 text-sm"
              >
                <span className="shrink-0 mt-0.5 text-xs font-medium px-2 py-0.5 rounded uppercase bg-navy-700 text-gray-300">
                  {String(ind.source || 'indicator')}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-200">
                      {String(ind.name || ind.indicator || '').replace(/_/g, ' ')}
                    </p>
                    {Boolean(ind.severity) && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold ${
                        ind.severity === 'high' ? 'bg-red-900/60 text-red-300' :
                        ind.severity === 'medium' ? 'bg-amber-900/60 text-amber-300' :
                        'bg-blue-900/60 text-blue-300'
                      }`}>
                        {String(ind.severity)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {String(ind.description || ind.reason || '')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation */}
      {data.explanation.length > 0 && (
        <div className="px-6 py-4 border-b border-navy-800">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Analysis Explanation</h4>
          <ul className="space-y-1">
            {data.explanation.map((line, i) => (
              <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                <span className="text-teal-500 mt-1">•</span>
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Individual Modality Breakdown toggle */}
      {data.modality_results && Object.keys(data.modality_results).length > 0 && (
        <div className="px-6 py-3">
          <button
            onClick={() => setShowModalityResults(!showModalityResults)}
            className="flex items-center gap-2 text-sm text-teal-400 hover:text-teal-300 transition-colors"
          >
            {showModalityResults ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showModalityResults ? 'Hide' : 'Show'} individual modality breakdown
          </button>
          {showModalityResults && (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.entries(data.modality_results).map(([mod, res]: [string, any]) => (
                <div key={mod} className="bg-navy-800 rounded-lg p-3 border border-navy-700">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold uppercase text-teal-400">{mod}</span>
                    <span className="text-xs text-gray-400">Prediction: <strong className="text-gray-200">{res.prediction}</strong></span>
                  </div>
                  <p className="text-xs text-gray-400">
                    Risk / Confidence: {res.risk_score !== undefined ? `${res.risk_score}/100` : `${(res.confidence * 100).toFixed(1)}%`}
                  </p>
                  {res.indicators && res.indicators.length > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      {res.indicators.length} indicator(s) found
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
