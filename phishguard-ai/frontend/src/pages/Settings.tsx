import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { VersionResponse, DetectionModelInfo } from '../types/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';

export default function Settings() {
  const [version, setVersion] = useState<VersionResponse | null>(null);
  const [models, setModels] = useState<DetectionModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const [v, m] = await Promise.all([api.getVersion(), api.getModels()]);
      setVersion(v);
      setModels(m.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-gray-400 mt-1">Application configuration and information</p>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchSettings} />}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="space-y-4">
          {/* Application Info */}
          <Section title="Application">
            <Row label="API Base URL" value={apiBaseUrl} />
            <Row label="Application Version" value={version?.version ?? '—'} />
            <Row label="Environment" value={version?.environment ?? '—'} />
            <Row label="Application Name" value={version?.name ?? '—'} />
          </Section>

          {/* Model Status */}
          <Section title="Detection Models">
            {models.map((m) => (
              <Row
                key={m.id}
                label={m.name}
                value={m.available ? 'Available' : 'Not implemented'}
              />
            ))}
          </Section>

          {/* Privacy */}
          <Section title="Privacy & Data Retention">
            <p className="text-sm text-gray-400 leading-relaxed">
              PhishGuard AI processes submitted content locally for phishing analysis.
              No data is sent to external services. Scan history is stored on-device
              only and can be cleared at any time. Uploaded files are not retained
              after analysis is complete.
            </p>
          </Section>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 space-y-3">
      <h2 className="text-sm font-medium text-gray-300">{title}</h2>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between text-sm gap-1">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-300 font-mono text-xs sm:text-sm">{value}</span>
    </div>
  );
}

