import { CheckCircle2, XCircle, MinusCircle } from 'lucide-react';

interface StatusRow {
  label: string;
  status: 'ok' | 'unavailable' | 'not_configured';
  detail?: string;
}

interface Props {
  rows: StatusRow[];
}

const ICON_MAP = {
  ok: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  unavailable: <XCircle className="h-4 w-4 text-red-400" />,
  not_configured: <MinusCircle className="h-4 w-4 text-gray-500" />,
};

export default function SystemStatus({ rows }: Props) {
  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-300 mb-4">System Status</h3>
      <ul className="space-y-3">
        {rows.map((r) => (
          <li key={r.label} className="flex items-center gap-3 text-sm">
            {ICON_MAP[r.status]}
            <span className="text-gray-300">{r.label}</span>
            {r.detail && <span className="ml-auto text-xs text-gray-500">{r.detail}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}

