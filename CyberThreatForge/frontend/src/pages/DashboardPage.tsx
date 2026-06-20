import { useEffect, useState } from 'react';
import { Shield, Activity, AlertTriangle, Globe, FileSearch, Users, ArrowUp, ArrowDown } from 'lucide-react';
import api from '../services/api';
import { ThreatCanvas3D, GraphNode, GraphEdge } from '../components/ThreatCanvas3D';
import { useAuthStore } from '../store/authStore';

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'critical';
  modules: number;
  activeInvestigations: number;
  uptime: number;
  modulesByStatus: Record<string, number>;
  activePipelines: number;
}

interface StatCard {
  title: string;
  value: string;
  change: number;
  icon: typeof Shield;
  color: string;
}

export function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [nodes] = useState<GraphNode[]>([]);
  const [edges] = useState<GraphEdge[]>([]);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const { data } = await api.get('/system/health');
        setHealth(data);
      } catch {
        // Health endpoint may not be available
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const stats: StatCard[] = [
    {
      title: 'Active Cases',
      value: String(health?.activeInvestigations ?? 0),
      change: 12,
      icon: Shield,
      color: 'text-cyan-400',
    },
    {
      title: 'Active Modules',
      value: String(health?.modules ?? 0),
      change: 0,
      icon: Activity,
      color: 'text-green-400',
    },
    {
      title: 'Threat Alerts',
      value: '7',
      change: -3,
      icon: AlertTriangle,
      color: 'text-amber-400',
    },
    {
      title: 'IOCs Tracked',
      value: '1,284',
      change: 45,
      icon: Globe,
      color: 'text-purple-400',
    },
  ];

  const recentActivity = [
    { time: '2 min ago', event: 'Memory dump analysis complete', case: 'CASE-2026-0421', severity: 'high' },
    { time: '15 min ago', event: 'APT29 TTP match found in network logs', case: 'CASE-2026-0419', severity: 'critical' },
    { time: '1 hr ago', event: 'Deepfake detected in submitted video evidence', case: 'CASE-2026-0418', severity: 'high' },
    { time: '3 hr ago', event: 'Dark web credential monitor: 12 new leaks', case: 'SYSTEM', severity: 'medium' },
    { time: '6 hr ago', event: 'Case CASE-2026-0415 closed with full attribution', case: 'CASE-2026-0415', severity: 'info' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Mission Dashboard</h1>
          <p className="text-sm text-gray-500">
            {user?.role.toUpperCase()} · {user?.department}
            {health && (
              <span className={`ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                health.status === 'healthy' ? 'bg-green-900/50 text-green-400' :
                health.status === 'degraded' ? 'bg-amber-900/50 text-amber-400' :
                'bg-red-900/50 text-red-400'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  health.status === 'healthy' ? 'bg-green-400' :
                  health.status === 'degraded' ? 'bg-amber-400' : 'bg-red-400'
                }`} />
                {health.status}
              </span>
            )}
          </p>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>System Uptime: {health ? Math.floor(health.uptime / 3600000) + 'h' : '--'}</div>
          <div>Active Pipelines: {health?.activePipelines ?? 0}</div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.title} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
              <span className={`flex items-center text-xs ${
                stat.change >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {stat.change >= 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                {Math.abs(stat.change)}%
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-100">{stat.value}</div>
            <div className="text-xs text-gray-500">{stat.title}</div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* 3D Threat Canvas */}
        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-lg overflow-hidden" style={{ height: 400 }}>
          <div className="p-3 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">Live Threat Graph</h2>
            <div className="flex gap-2">
              <button className="px-2 py-1 text-xs bg-gray-800 text-gray-400 rounded hover:bg-gray-700">2D</button>
              <button className="px-2 py-1 text-xs bg-cyan-800 text-cyan-300 rounded">3D</button>
              <button className="px-2 py-1 text-xs bg-gray-800 text-gray-400 rounded hover:bg-gray-700">VR</button>
            </div>
          </div>
          <ThreatCanvas3D nodes={nodes} edges={edges} />
        </div>

        {/* Recent Activity */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-3 border-b border-gray-800">
            <h2 className="text-sm font-medium text-gray-300">Recent Activity</h2>
          </div>
          <div className="divide-y divide-gray-800">
            {recentActivity.map((item, i) => (
              <div key={i} className="p-3 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-300 truncate">{item.event}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{item.case}</p>
                  </div>
                  <span className={`ml-2 px-1.5 py-0.5 rounded text-xs font-medium ${
                    item.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                    item.severity === 'high' ? 'bg-amber-900/50 text-amber-400' :
                    item.severity === 'medium' ? 'bg-blue-900/50 text-blue-400' :
                    'bg-gray-800 text-gray-500'
                  }`}>
                    {item.severity}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">{item.time}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Module Health Bar */}
      {health && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-medium text-gray-300 mb-3">Module Health</h2>
          <div className="flex gap-4">
            {Object.entries(health.modulesByStatus).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  status === 'active' ? 'bg-green-400' :
                  status === 'idle' ? 'bg-gray-500' :
                  status === 'learning' ? 'bg-blue-400' :
                  status === 'error' ? 'bg-red-400' :
                  'bg-amber-400'
                }`} />
                <span className="text-xs text-gray-400 capitalize">{status}: {count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
