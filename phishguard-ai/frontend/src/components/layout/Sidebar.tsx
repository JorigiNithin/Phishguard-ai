import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  History,
  Cpu,
  Settings as SettingsIcon,
  Shield,
  Menu,
  X,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useState } from 'react';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: Search },
  { to: '/history', label: 'Scan History', icon: History },
  { to: '/models', label: 'Models', icon: Cpu },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

interface Props {
  backendOnline: boolean;
}

export default function Sidebar({ backendOnline }: Props) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navContent = (
    <>
      {/* Logo / brand */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-navy-800">
        <Shield className="h-7 w-7 text-teal-400" />
        <span className="text-lg font-bold tracking-tight">
          Phish<span className="text-teal-400">Guard</span> AI
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-navy-800 text-teal-400'
                  : 'text-gray-400 hover:bg-navy-800/60 hover:text-gray-200'
              }`
            }
          >
            <Icon className="h-4.5 w-4.5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-navy-800 space-y-2">
        <div className="flex items-center gap-2 text-xs">
          {backendOnline ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-emerald-400">Backend connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-red-400" />
              <span className="text-red-400">Backend unavailable</span>
            </>
          )}
        </div>
        <p className="text-[11px] text-gray-500">v0.1.0</p>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="lg:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-navy-900 text-gray-300 hover:bg-navy-800"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation"
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/50"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen w-60 flex flex-col
          bg-navy-900 border-r border-navy-800
          transition-transform lg:translate-x-0
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {navContent}
      </aside>
    </>
  );
}

