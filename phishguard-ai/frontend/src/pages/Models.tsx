import { useEffect, useState } from 'react';
import { Link, Mail, Image, Code2, Layers } from 'lucide-react';
import { api } from '../services/api';
import type { DetectionModelInfo, Modality } from '../types/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';

const ICONS: Record<Modality, React.ReactNode> = {
  url: <Link className="h-6 w-6" />,
  email: <Mail className="h-6 w-6" />,
  screenshot: <Image className="h-6 w-6" />,
  html: <Code2 className="h-6 w-6" />,
  multimodal: <Layers className="h-6 w-6" />,
};

export default function Models() {
  const [models, setModels] = useState<DetectionModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getModels();
      setModels(res.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Model Status</h1>
        <p className="text-sm text-gray-400 mt-1">
          Detection model implementation and training status
        </p>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchModels} />}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {models.map((m) => (
            <div
              key={m.id}
              className="bg-navy-900 border border-navy-800 rounded-xl p-5 space-y-4"
            >
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-navy-800 text-teal-400">
                  {ICONS[m.modality]}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-200">{m.name}</h3>
                  <p className="text-xs text-gray-500 uppercase">{m.modality} modality</p>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <Row label="Implementation" value={statusLabel(m.status)} />
                <Row label="Model Type" value={m.model_type ?? 'Not determined'} />
                <Row label="Training Status" value={m.training_status ?? 'Not started'} />
                <Row label="Available" value={m.available ? 'Yes' : 'No'} />
              </div>

              <p className="text-xs text-gray-500">{m.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-300">{value}</span>
    </div>
  );
}

function statusLabel(status: string): string {
  switch (status) {
    case 'not_implemented':
      return 'Not implemented';
    case 'implemented':
      return 'Implemented';
    case 'training':
      return 'Training';
    case 'trained':
      return 'Trained';
    case 'error':
      return 'Error';
    default:
      return status;
  }
}

