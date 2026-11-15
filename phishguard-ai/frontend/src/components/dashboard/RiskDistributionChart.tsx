import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { RiskDistributionEntry } from '../../types/api';

interface Props {
  data: RiskDistributionEntry[];
}

export default function RiskDistributionChart({ data }: Props) {
  const hasData = data.some((d) => d.value > 0);

  if (!hasData) {
    return (
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">Risk Distribution</h3>
        <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
          No scan data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-300 mb-4">Risk Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e2d7d',
              border: '1px solid #2235a3',
              borderRadius: '8px',
              fontSize: '12px',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap justify-center gap-4 mt-2">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            {entry.name}
          </div>
        ))}
      </div>
    </div>
  );
}

