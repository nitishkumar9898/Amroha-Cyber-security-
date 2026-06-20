import { useState, useEffect } from 'react';
import { Users as UsersIcon, Shield, Key, Activity, Database, Lock, FileText } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  department: string;
  station: string | null;
  mfa_enabled: boolean;
  last_login_at: string | null;
  created_at: string;
}

export function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [activeTab, setActiveTab] = useState<'users' | 'modules' | 'audit' | 'security'>('users');
  const user = useAuthStore((s) => s.user);

  const tabs = [
    { id: 'users' as const, label: 'User Management', icon: UsersIcon },
    { id: 'modules' as const, label: 'Module Registry', icon: Activity },
    { id: 'audit' as const, label: 'Audit Log', icon: FileText },
    { id: 'security' as const, label: 'Security Config', icon: Lock },
  ];

  useEffect(() => {
    if (activeTab === 'users') {
      // fetchUsers();
    }
  }, [activeTab]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Admin Console</h1>
        <p className="text-sm text-gray-500">{user?.role.toUpperCase()} · System Administration</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 rounded-lg p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm transition-colors ${
              activeTab === tab.id
                ? 'bg-cyan-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">Registered Users</h2>
            <button className="px-3 py-1.5 text-xs bg-cyan-600 text-white rounded hover:bg-cyan-500">
              + Add User
            </button>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left p-3 font-medium">Name</th>
                <th className="text-left p-3 font-medium">Email</th>
                <th className="text-left p-3 font-medium">Role</th>
                <th className="text-left p-3 font-medium">Department</th>
                <th className="text-left p-3 font-medium">MFA</th>
                <th className="text-left p-3 font-medium">Last Login</th>
                <th className="text-left p-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-gray-600">
                    <UsersIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    No users registered yet
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-800 hover:bg-gray-800/30">
                    <td className="p-3 text-gray-300">{u.name}</td>
                    <td className="p-3 text-gray-400">{u.email}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        u.role === 'admin' || u.role === 'super_admin' ? 'bg-red-900/50 text-red-400' :
                        u.role === 'cbi' ? 'bg-purple-900/50 text-purple-400' :
                        u.role === 'nia' ? 'bg-blue-900/50 text-blue-400' :
                        'bg-gray-800 text-gray-400'
                      }`}>{u.role.toUpperCase()}</span>
                    </td>
                    <td className="p-3 text-gray-400">{u.department}</td>
                    <td className="p-3">
                      <span className={`text-xs ${u.mfa_enabled ? 'text-green-400' : 'text-gray-600'}`}>
                        {u.mfa_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </td>
                    <td className="p-3 text-gray-500 text-xs">{u.last_login_at ?? 'Never'}</td>
                    <td className="p-3">
                      <div className="flex gap-2">
                        <button className="text-xs text-cyan-400 hover:text-cyan-300">Edit</button>
                        <button className="text-xs text-red-400 hover:text-red-300">Disable</button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'modules' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Module Registry Dashboard — 83+ plugin slots available</p>
          <p className="text-xs text-gray-600 mt-1">View module health, enable/disable, hot-reload</p>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500">
          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Immutable Audit Log — HMAC-chained, tamper-evident</p>
          <p className="text-xs text-gray-600 mt-1">Search by actor, action, resource, or time range</p>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Key className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-medium text-gray-300">Encryption</h3>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-gray-500">At Rest</span><span className="text-green-400">AES-256-GCM</span></div>
              <div className="flex justify-between"><span className="text-gray-500">In Transit</span><span className="text-green-400">TLS 1.3</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Key Exchange</span><span className="text-green-400">CRYSTALS-Kyber</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Signatures</span><span className="text-green-400">CRYSTALS-Dilithium</span></div>
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-medium text-gray-300">Access Control</h3>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-gray-500">Auth Method</span><span className="text-gray-300">JWT + OAuth2 + MFA</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Session Timeout</span><span className="text-gray-300">15 min</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Rate Limit</span><span className="text-gray-300">100 req/min</span></div>
              <div className="flex justify-between"><span className="text-gray-500">MFA Required For</span><span className="text-amber-400">NIA, CBI, Admin</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
