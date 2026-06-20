import { useState } from 'react';
import { User, Shield, Key, Bell, Smartphone, LogOut, Save } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const [activeSection, setActiveSection] = useState<'profile' | 'security' | 'notifications'>('profile');

  const sections = [
    { id: 'profile' as const, label: 'Profile', icon: User },
    { id: 'security' as const, label: 'Security', icon: Shield },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">Manage your account, security, and preferences</p>
      </div>

      <div className="flex gap-1 bg-gray-900 rounded-lg p-1 w-fit">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm transition-colors ${
              activeSection === s.id ? 'bg-cyan-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <s.icon className="w-4 h-4" />
            {s.label}
          </button>
        ))}
      </div>

      {activeSection === 'profile' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-6">
          <div className="flex items-center gap-4 pb-4 border-b border-gray-800">
            <div className="w-16 h-16 rounded-full bg-cyan-600/20 flex items-center justify-center">
              <User className="w-8 h-8 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-200">{user?.name ?? 'User'}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
              <span className="inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium bg-cyan-900/50 text-cyan-400">
                {user?.role?.toUpperCase()}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Name', value: user?.name ?? '--' },
              { label: 'Email', value: user?.email ?? '--' },
              { label: 'Role', value: user?.role?.toUpperCase() ?? '--' },
              { label: 'Department', value: user?.department ?? '--' },
              { label: 'Badge Number', value: 'CTF-2026-0421' },
              { label: 'Member Since', value: 'June 2026' },
            ].map((f) => (
              <div key={f.label}>
                <label className="text-xs text-gray-500 block mb-1">{f.label}</label>
                <input
                  type="text"
                  defaultValue={f.value}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300"
                  readOnly={f.label !== 'Name'}
                />
              </div>
            ))}
          </div>
          <div className="pt-4 border-t border-gray-800">
            <button className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded text-sm hover:bg-cyan-500">
              <Save className="w-4 h-4" /> Save Changes
            </button>
          </div>
        </div>
      )}

      {activeSection === 'security' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Key className="w-4 h-4 text-cyan-400" /> Authentication
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded">
                <div>
                  <p className="text-sm text-gray-200">Password</p>
                  <p className="text-xs text-gray-500">Last changed 30 days ago</p>
                </div>
                <button className="text-xs text-cyan-400 hover:text-cyan-300">Change</button>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded">
                <div>
                  <p className="text-sm text-gray-200">Two-Factor Authentication (TOTP)</p>
                  <p className="text-xs text-gray-500">Add an extra layer of security</p>
                </div>
                <button className="px-3 py-1 text-xs bg-cyan-600 text-white rounded hover:bg-cyan-500">Enable</button>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded">
                <div>
                  <p className="text-sm text-gray-200">Active Sessions</p>
                  <p className="text-xs text-gray-500">2 active sessions across devices</p>
                </div>
                <button className="text-xs text-red-400 hover:text-red-300">Revoke All</button>
              </div>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-cyan-400" /> Registered Devices
            </h3>
            {[
              { name: 'Investigation Workstation #1', os: 'Windows 11', lastUsed: '2 hours ago' },
              { name: 'Mobile Evidence Kit', os: 'Ubuntu 24.04', lastUsed: '1 day ago' },
            ].map((d, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded mb-2">
                <div>
                  <p className="text-sm text-gray-200">{d.name}</p>
                  <p className="text-xs text-gray-500">{d.os} · Last used: {d.lastUsed}</p>
                </div>
                <span className="w-2 h-2 rounded-full bg-green-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === 'notifications' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
          {[
            { label: 'Critical Alert Escalation', desc: 'Push notification + SMS for critical threats', enabled: true },
            { label: 'Investigation Completion', desc: 'Email when pipeline finishes', enabled: true },
            { label: 'New IOC Match', desc: 'Alert when new IOCs match active cases', enabled: false },
            { label: 'Weekly Threat Briefing', desc: 'Email summary of new threats and IOCs', enabled: true },
            { label: 'System Health Degradation', desc: 'Alert when module health drops below threshold', enabled: true },
          ].map((n, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-800/50 rounded">
              <div>
                <p className="text-sm text-gray-200">{n.label}</p>
                <p className="text-xs text-gray-500">{n.desc}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked={n.enabled} className="sr-only peer" />
                <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-600" />
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
