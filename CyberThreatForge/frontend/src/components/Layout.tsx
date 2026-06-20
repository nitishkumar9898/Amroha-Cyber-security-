import { Outlet, NavLink } from 'react-router-dom';
import { Shield, FolderSearch, FileSearch, Globe, Users, LogOut, User } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: Shield },
  { to: '/cases', label: 'Cases', icon: FolderSearch },
  { to: '/evidence', label: 'Evidence', icon: FileSearch },
  { to: '/threat-intel', label: 'Threat Intel', icon: Globe },
  { to: '/admin', label: 'Admin', icon: Users, adminOnly: true },
];

export function Layout() {
  const { user, logout } = useAuthStore();

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            CyberThreatForge
          </h1>
          <p className="text-xs text-gray-500 mt-1">{user?.role?.toUpperCase()} — {user?.department}</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map(({ to, label, icon: Icon, adminOnly }) => {
            if (adminOnly && user?.role !== 'admin' && user?.role !== 'super_admin') return null;
            return (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive ? 'bg-cyan-600/20 text-cyan-400' : 'text-gray-400 hover:bg-gray-800'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {label}
              </NavLink>
            );
          })}
        </nav>
        <div className="p-4 border-t border-gray-800 space-y-1">
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-cyan-600/20 text-cyan-400' : 'text-gray-400 hover:bg-gray-800'
              }`
            }
          >
            <User className="w-4 h-4" />
            Settings
          </NavLink>
          <button onClick={logout} className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-400 w-full px-3 py-2 rounded-lg">
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
