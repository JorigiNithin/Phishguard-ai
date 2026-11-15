import { Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import { api } from '../../services/api';

export default function AppLayout() {
  const [backendOnline, setBackendOnline] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        await api.getHealth();
        if (!cancelled) setBackendOnline(true);
      } catch {
        if (!cancelled) setBackendOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar backendOnline={backendOnline} />
      <main className="flex-1 overflow-y-auto p-4 lg:p-8">
        <Outlet context={{ backendOnline }} />
      </main>
    </div>
  );
}

