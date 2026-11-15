import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ExplainableIndicator, ScanDetailResponse, ScanHistoryItem } from '../types/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorBanner from '../components/common/ErrorBanner';
import EmptyState from '../components/common/EmptyState';

export default function History() {
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [scanType, setScanType] = useState('');
  const [prediction, setPrediction] = useState('');
  const [search, setSearch] = useState('');
  const [selectedScan, setSelectedScan] = useState<ScanDetailResponse | null>(null);
  const [explanations, setExplanations] = useState<ExplainableIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getScanHistory({
        scan_type: scanType || undefined,
        prediction: prediction || undefined,
        search: search || undefined,
        page,
        page_size: pageSize,
      });
      setScans(res.scans);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, scanType, prediction, search]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const openScan = async (scanId: string) => {
    try {
      const [detail, explainRes] = await Promise.all([
        api.getScanDetail(scanId),
        api.getScanExplanation(scanId).catch(() => ({ explanation: [] })),
      ]);
      setSelectedScan(detail);
      setExplanations(explainRes.explanation);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan detail');
    }
  };

  const handleDelete = async (scanId: string) => {
    const confirmed = window.confirm('Delete this scan from history?');
    if (!confirmed) return;

    try {
      await api.deleteScan(scanId);
      setSelectedScan(null);
      setPage(1);
      await fetchHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete scan');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Scan History</h1>
        <p className="text-sm text-gray-400 mt-1">Review persisted phishing analyses</p>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchHistory} />}

      <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search target or type"
            className="bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder:text-gray-500"
          />
          <select
            value={scanType}
            onChange={(e) => {
              setScanType(e.target.value);
              setPage(1);
            }}
            className="bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-sm text-gray-200"
          >
            <option value="">All scan types</option>
            <option value="url">URL</option>
            <option value="email">Email</option>
            <option value="screenshot">Screenshot</option>
            <option value="html">HTML</option>
            <option value="multimodal">Multimodal</option>
          </select>
          <select
            value={prediction}
            onChange={(e) => {
              setPrediction(e.target.value);
              setPage(1);
            }}
            className="bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-sm text-gray-200"
          >
            <option value="">All predictions</option>
            <option value="phishing">Phishing</option>
            <option value="suspicious">Suspicious</option>
            <option value="safe">Safe</option>
            <option value="legitimate">Legitimate</option>
          </select>
          <div className="flex items-center justify-end text-sm text-gray-400">
            {total} total scans
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : scans.length === 0 ? (
        <EmptyState
          title="No scan history"
          message="Completed scans will appear here. Run an analysis from the Analyze page to populate the database."
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-[1.3fr_0.7fr] gap-4">
          <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-navy-800 text-left text-gray-400">
                  <th className="px-4 py-3 font-medium">Scan ID</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Prediction</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id} className="border-b border-navy-800/50 hover:bg-navy-800/30">
                    <td className="px-4 py-3 text-gray-300">
                      <button className="text-teal-400 hover:text-teal-300" onClick={() => openScan(s.id)}>
                        {s.id.slice(0, 8)}
                      </button>
                    </td>
                    <td className="px-4 py-3 capitalize text-gray-300">{s.scan_type}</td>
                    <td className="px-4 py-3 text-gray-300">{s.prediction}</td>
                    <td className="px-4 py-3 text-gray-300">{s.risk_score}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{new Date(s.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <button
                        className="text-red-400 hover:text-red-300"
                        onClick={() => handleDelete(s.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedScan ? (
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 space-y-4">
              <div className="flex items-center justify-between gap-2 border-b border-navy-800 pb-3">
                <div>
                  <h3 className="font-semibold text-gray-100">Scan Detail</h3>
                  <p className="text-xs text-gray-400 font-mono mt-0.5">{selectedScan.id}</p>
                </div>
                <button className="text-sm text-gray-400 hover:text-gray-200" onClick={() => setSelectedScan(null)}>
                  Close
                </button>
              </div>
              <dl className="grid grid-cols-2 gap-2 text-sm text-gray-300">
                <div><dt className="text-xs text-gray-500 uppercase">Type</dt><dd className="capitalize">{selectedScan.scan_type}</dd></div>
                <div><dt className="text-xs text-gray-500 uppercase">Prediction</dt><dd className="font-semibold text-teal-400 capitalize">{selectedScan.prediction}</dd></div>
                <div><dt className="text-xs text-gray-500 uppercase">Risk Score</dt><dd className="font-semibold">{selectedScan.risk_score} / 100</dd></div>
                <div><dt className="text-xs text-gray-500 uppercase">Status</dt><dd className="capitalize">{selectedScan.status}</dd></div>
                {selectedScan.target_summary && (
                  <div className="col-span-2"><dt className="text-xs text-gray-500 uppercase">Target</dt><dd className="truncate text-xs font-mono text-gray-400">{selectedScan.target_summary}</dd></div>
                )}
                {selectedScan.model_used && (
                  <div className="col-span-2"><dt className="text-xs text-gray-500 uppercase">Model</dt><dd className="text-xs text-gray-400">{selectedScan.model_used}</dd></div>
                )}
                <div className="col-span-2"><dt className="text-xs text-gray-500 uppercase">Timestamp</dt><dd className="text-xs text-gray-400">{new Date(selectedScan.created_at).toLocaleString()}</dd></div>
              </dl>

              {/* Explainable AI breakdown */}
              {explanations.length > 0 && (
                <div className="border-t border-navy-800 pt-3">
                  <h4 className="text-xs uppercase tracking-wide text-teal-400 font-semibold mb-2">Explainable AI Breakdown</h4>
                  <div className="space-y-2 max-h-56 overflow-y-auto">
                    {explanations.map((exp, idx) => (
                      <div key={idx} className="bg-navy-800/80 border border-navy-700 rounded-lg p-2.5 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-200">{exp.indicator}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            exp.impact === 'high' ? 'bg-red-900/60 text-red-300' :
                            exp.impact === 'medium' ? 'bg-amber-900/60 text-amber-300' :
                            'bg-blue-900/60 text-blue-300'
                          }`}>
                            {exp.impact}
                          </span>
                        </div>
                        <p className="text-gray-400">{exp.reason}</p>
                        <span className="inline-block text-[10px] text-gray-500 uppercase">Source: {exp.source}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* General explanation lines */}
              {selectedScan.explanation.length > 0 && (
                <div className="border-t border-navy-800 pt-3">
                  <h4 className="text-xs uppercase tracking-wide text-gray-500 mb-2">Analysis Summary</h4>
                  <ul className="list-disc pl-5 text-xs text-gray-400 space-y-1">
                    {selectedScan.explanation.map((line, idx) => <li key={`${line}-${idx}`}>{line}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-navy-900 border border-navy-800 rounded-xl p-4 text-sm text-gray-400 flex items-center justify-center">
              Select a scan to view details.
            </div>
          )}
        </div>
      )}

      {!loading && total > 0 && (
        <div className="flex items-center justify-between gap-3 text-sm text-gray-400">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-2 rounded-lg border border-navy-700 disabled:opacity-50"
          >
            Previous
          </button>
          <span>
            Page {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-2 rounded-lg border border-navy-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

