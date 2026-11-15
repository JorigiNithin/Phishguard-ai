import type { ReactNode } from 'react';

interface Props {
  title: string;
  value: string | number;
  icon: ReactNode;
  subtitle?: string;
  accent?: string; // tailwind text-color class
}

export default function StatCard({ title, value, icon, subtitle, accent = 'text-teal-400' }: Props) {
  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 flex items-start gap-4">
      <div className={`p-2.5 rounded-lg bg-navy-800 ${accent}`}>{icon}</div>
      <div>
        <p className="text-sm text-gray-400">{title}</p>
        <p className="text-2xl font-semibold mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

