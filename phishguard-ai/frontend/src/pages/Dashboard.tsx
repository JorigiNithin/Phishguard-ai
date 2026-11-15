import { useEffect, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  Activity,
  ShieldAlert,
  AlertTriangle,
  Cpu,
  Wifi,
  WifiOff,
  Search,
} from 'lucide-react';
import { api } from '../services/api';
import type { StatisticsResponse, DetectionModelInfo } from '../types/api';
import StatCard from '../components/common/StatCard';
import ErrorBanner from '../components/common/ErrorBanner';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import RiskDistributionChart from '../components/dashboard/RiskDistributionChart';
import DetectionModules from '../components/dashboard/DetectionModules';
import SystemStatus from '../components/dashboard/SystemStatus';

interface OutletCtx {
  backendOnline: boolean;
}

export default function Dashboard() {
  const { backendOnline } = useOutletContext<OutletCtx>();
  const navigate = useNavigate();

  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [models, setModels] = useState<DetectionModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, modelsRes] = await Promise.all([
        api.getDashboardStatistics(),
        api.getModels(),
      ]);
      setStats(statsRes);
      setModels(modelsRes.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const systemRows = [
    {
      label: 'Backend API',
      status: backendOnline ? ('ok' as const) : ('unavailable' as const),
      detail: backendOnline ? 'Connected' : 'Offline',
    },
    {
      label: 'Database',
      status: backendOnline ? ('ok' as const) : ('unavailable' as const),
      detail: backendOnline ? 'SQLite ready' : 'Unavailable',
    },
    {
      label: 'Detection Models',
      status: models.length > 0 ? ('ok' as const) : ('unavailable' as const),
      detail: models.length > 0 ? `${models.length} detector(s) registered` : 'None registered',
    },
    { label: 'Application Version', status: 'ok' as const, detail: 'v0.1.0' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">
            Multimodal phishing detection overview
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs">
            {backendOnline ? (
              <>
                <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-red-400" />
                <span className="text-red-400">Backend unavailable</span>
              </>
            )}
          </span>
          <button
            onClick={() => navigate('/analyze')}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Search className="h-4 w-4" />
            Analyze
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchData} />}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Scans"
              value={stats?.total_scans ?? 0}
              icon={<Activity className="h-5 w-5" />}
            />
            <StatCard
              title="Phishing Detections"
              value={stats?.high_risk ?? 0}
              icon={<ShieldAlert className="h-5 w-5" />}
              accent="text-red-400"
            />
            <StatCard
              title="Safe Detections"
              value={stats?.safe ?? 0}
              icon={<Activity className="h-5 w-5" />}
              accent="text-emerald-400"
            />
            <StatCard
              title="Suspicious Detections"
              value={stats?.suspicious ?? 0}
              icon={<AlertTriangle className="h-5 w-5" />}
              accent="text-amber-400"
            />
          </div>

          {/* Charts & modules row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RiskDistributionChart data={stats?.risk_distribution ?? []} />
            <div className="space-y-4">
              <DetectionModules
                modules={models.map((m) => ({
                  name: m.name,
                  modality: m.modality,
                  status: m.status,
                }))}
              />
              <div className="bg-navy-900 border border-navy-800 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-gray-200 mb-3">Modality Usage</h3>
                {stats?.modality_usage && Object.keys(stats.modality_usage).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(stats.modality_usage).map(([name, count]) => (
                      <div key={name} className="flex items-center justify-between text-sm text-gray-300">
                        <span className="capitalize">{name}</span>
                        <span className="font-medium text-teal-400">{count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No modality data yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* Recent scans */}
          {stats?.recent_scans && stats.recent_scans.length > 0 ? (
            <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-navy-800">
                <h3 className="text-sm font-semibold text-gray-200">Recent Scans</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-navy-800 text-left text-gray-400">
                      <th className="px-4 py-3 font-medium">Scan ID</th>
                      <th className="px-4 py-3 font-medium">Type</th>
                      <th className="px-4 py-3 font-medium">Prediction</th>
                      <th className="px-4 py-3 font-medium">Risk</th>
                      <th className="px-4 py-3 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_scans.map((scan) => (
                      <tr key={scan.id} className="border-b border-navy-800/50 hover:bg-navy-800/30">
                        <td className="px-4 py-3 text-gray-300">{scan.id.slice(0, 8)}</td>
                        <td className="px-4 py-3 capitalize text-gray-300">{scan.scan_type}</td>
                        <td className="px-4 py-3 text-gray-300">{scan.prediction}</td>
                        <td className="px-4 py-3 text-gray-300">{scan.risk_score}</td>
                        <td className="px-4 py-3 text-gray-500">{new Date(scan.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No recent scan activity"
              message="Completed scans will appear here. Start an analysis from the Analyze page."
            />
          )}

          {/* System status */}
          <SystemStatus rows={systemRows} />
        </>
      )}
    </div>
  );
}

