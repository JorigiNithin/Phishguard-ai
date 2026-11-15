import { Inbox } from 'lucide-react';

interface Props {
  title: string;
  message: string;
}

export default function EmptyState({ title, message }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-full bg-navy-800 mb-4">
        <Inbox className="h-8 w-8 text-gray-500" />
      </div>
      <h3 className="text-lg font-medium text-gray-300">{title}</h3>
      <p className="text-sm text-gray-500 mt-1 max-w-sm">{message}</p>
    </div>
  );
}

