import { Link, Globe, Mail, Image, Code2, Layers } from 'lucide-react';
import type { Modality, ModelStatus } from '../../types/api';

interface Module {
  name: string;
  modality: Modality;
  status: ModelStatus;
}

interface Props {
  modules: Module[];
}

const ICONS: Record<Modality, React.ReactNode> = {
  url: <Link className="h-5 w-5" />,
  email: <Mail className="h-5 w-5" />,
  screenshot: <Image className="h-5 w-5" />,
  html: <Code2 className="h-5 w-5" />,
  multimodal: <Layers className="h-5 w-5" />,
};

const STATUS_LABEL: Record<ModelStatus, { text: string; color: string }> = {
  not_implemented: { text: 'Coming in a later development section', color: 'text-gray-500' },
  implemented: { text: 'Implemented', color: 'text-blue-400' },
  training: { text: 'Training', color: 'text-amber-400' },
  trained: { text: 'Ready', color: 'text-emerald-400' },
  error: { text: 'Error', color: 'text-red-400' },
};

export default function DetectionModules({ modules }: Props) {
  return (
    <div className="bg-navy-900 border border-navy-800 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-300 mb-4">Detection Modules</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {modules.map((m) => {
          const st = STATUS_LABEL[m.status];
          return (
            <div
              key={m.modality}
              className="flex items-start gap-3 bg-navy-800/50 border border-navy-700/50 rounded-lg p-3"
            >
              <div className="p-2 rounded-lg bg-navy-800 text-teal-400">{ICONS[m.modality]}</div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-200">{m.name}</p>
                <p className={`text-xs mt-0.5 ${st.color}`}>{st.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

