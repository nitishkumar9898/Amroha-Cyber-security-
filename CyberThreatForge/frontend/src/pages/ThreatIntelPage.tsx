import { useState } from 'react';
import { Globe, Search, AlertTriangle, TrendingUp, Users, Shield, ExternalLink, Radar } from 'lucide-react';

const MOCK_IOCS = [
  { type: 'ip', value: '185.234.72.18', severity: 'critical', source: 'darkweb', firstSeen: '2026-06-18', tags: ['c2', 'lockbit'] },
  { type: 'domain', value: 'malware-c2-topkek[.]ru', severity: 'high', source: 'sandbox', firstSeen: '2026-06-15', tags: ['ransomware'] },
  { type: 'hash', value: 'e3b0c44298fc1c149afbf4c8996fb924...', severity: 'critical', source: 'analysis', firstSeen: '2026-06-14', tags: ['lockbit-variant'] },
  { type: 'email', value: 'researcher@protonmail[.]ch', severity: 'medium', source: 'forum', firstSeen: '2026-06-10', tags: ['apt'] },
  { type: 'cve', value: 'CVE-2026-1234', severity: 'high', source: 'feed', firstSeen: '2026-06-08', tags: ['critical', 'exploit'] },
];

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-900/50 text-red-400',
  high: 'bg-amber-900/50 text-amber-400',
  medium: 'bg-blue-900/50 text-blue-400',
  low: 'bg-gray-800 text-gray-400',
};

const RECENT_ALERTS = [
  { title: 'APT29 Infrastructure Match — LockBit variant C2 overlaps with known Cozy Bear TTPs', severity: 'critical', time: '10m ago' },
  { title: 'New Ransomware Leak Site — 12 Indian organizations listed on Clop dark web portal', severity: 'high', time: '45m ago' },
  { title: 'Dark Web Credential Dump — 50K Indian govt employee emails leaked on breach forum', severity: 'critical', time: '2h ago' },
  { title: 'CVE-2026-1234 Exploit PoC Published — Affects government web portals', severity: 'high', time: '4h ago' },
];

export function ThreatIntelPage() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Threat Intelligence</h1>
        <p className="text-sm text-gray-500">Real-time threat monitoring · IOC tracking · Dark web intelligence</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Active IOCs', value: '1,284', change: '+47', icon: Radar, color: 'text-red-400' },
          { label: 'Dark Web Sources', value: '12', change: 'Active', icon: Globe, color: 'text-purple-400' },
          { label: 'Threat Feeds', value: '8', change: 'Online', icon: TrendingUp, color: 'text-blue-400' },
          { label: 'APT Groups Tracked', value: '34', change: '+2', icon: Users, color: 'text-amber-400' },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <s.icon className={`w-5 h-5 ${s.color}`} />
              <span className="text-xs text-gray-600">{s.change}</span>
            </div>
            <div className="text-2xl font-bold text-gray-100">{s.value}</div>
            <div className="text-xs text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* IOC Feed */}
        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-800">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-gray-300">IOC Feed</h2>
              <button className="text-xs text-cyan-400 hover:text-cyan-300">View All</button>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text" placeholder="Search IOCs..."
                value={search} onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-cyan-600"
              />
            </div>
          </div>
          <div className="divide-y divide-gray-800">
            {MOCK_IOCS.map((ioc, i) => (
              <div key={i} className="p-4 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium uppercase ${SEVERITY_COLORS[ioc.severity]}`}>{ioc.severity}</span>
                      <span className="text-xs text-gray-500">{ioc.type.toUpperCase()}</span>
                      <span className="text-sm font-mono text-gray-200">{ioc.value}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-600">
                      <span>Source: {ioc.source}</span>
                      <span>First seen: {ioc.firstSeen}</span>
                      <span className="flex gap-1">
                        {ioc.tags.map((t, j) => (
                          <span key={j} className="px-1 bg-gray-800 rounded text-gray-500">{t}</span>
                        ))}
                      </span>
                    </div>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-600 hover:text-gray-400 cursor-pointer" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">Recent Alerts</h2>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="divide-y divide-gray-800">
            {RECENT_ALERTS.map((alert, i) => (
              <div key={i} className="p-3 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-start gap-2">
                  <span className={`mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                    alert.severity === 'critical' ? 'bg-red-400' : 'bg-amber-400'
                  }`} />
                  <div>
                    <p className="text-xs text-gray-300 leading-relaxed">{alert.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{alert.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
