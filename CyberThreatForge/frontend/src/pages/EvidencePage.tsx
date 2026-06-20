import { useState } from 'react';
import { Search, Filter, FileSearch, Upload, Shield, Hash, Calendar, HardDrive } from 'lucide-react';

const EVIDENCE_TYPES = [
  'device_image', 'log_file', 'memory_dump', 'network_capture',
  'malware_sample', 'document', 'image', 'video', 'audio',
];

const MOCK_EVIDENCE = [
  { id: 'e1', type: 'memory_dump', case: 'CASE-2026-0421', description: 'RAM dump — Govt Portal Server #3', size: '4.0 GB', hash: 'a1b2c3d4...', date: '2026-06-15', status: 'analyzed' },
  { id: 'e2', type: 'network_capture', case: 'CASE-2026-0421', description: 'PCAP — C2 traffic analysis', size: '100 MB', hash: 'e5f6g7h8...', date: '2026-06-15', status: 'analyzed' },
  { id: 'e3', type: 'malware_sample', case: 'CASE-2026-0421', description: 'LockBit variant — ransom note', size: '5 MB', hash: 'i9j0k1l2...', date: '2026-06-15', status: 'analyzed' },
  { id: 'e4', type: 'log_file', case: 'CASE-2026-0419', description: 'Auth logs — brute force attempt', size: '250 MB', hash: 'm3n4o5p6...', date: '2026-06-14', status: 'processing' },
  { id: 'e5', type: 'device_image', case: 'CASE-2026-0418', description: 'Disk image — suspect laptop E01', size: '128 GB', hash: 'q7r8s9t0...', date: '2026-06-13', status: 'ingested' },
];

export function EvidencePage() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  const filtered = MOCK_EVIDENCE.filter((e) => {
    const matchesSearch = e.description.toLowerCase().includes(search.toLowerCase()) ||
      e.case.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === 'all' || e.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Evidence Locker</h1>
          <p className="text-sm text-gray-500">{MOCK_EVIDENCE.length} items across {new Set(MOCK_EVIDENCE.map(e => e.case)).size} cases</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg text-sm hover:bg-cyan-500 transition-colors">
          <Upload className="w-4 h-4" />
          Upload Evidence
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search evidence by description, case, or hash..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-cyan-600"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-400 focus:outline-none focus:border-cyan-600"
          >
            <option value="all">All Types</option>
            {EVIDENCE_TYPES.map((t) => (
              <option key={t} value={t}>{t.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3">
        {filtered.map((ev) => (
          <div key={ev.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors cursor-pointer">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <FileSearch className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-medium text-gray-200">{ev.description}</h3>
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    ev.status === 'analyzed' ? 'bg-green-900/50 text-green-400' :
                    ev.status === 'processing' ? 'bg-blue-900/50 text-blue-400' :
                    'bg-gray-800 text-gray-400'
                  }`}>{ev.status}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-600 mt-1">
                  <span className="flex items-center gap-1"><Shield className="w-3 h-3" />{ev.case}</span>
                  <span className="flex items-center gap-1"><HardDrive className="w-3 h-3" />{ev.size}</span>
                  <span className="flex items-center gap-1"><Hash className="w-3 h-3" />{ev.hash}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{ev.date}</span>
                  <span className="px-1.5 py-0.5 rounded text-xs bg-gray-800 text-gray-500">{ev.type.replace('_', ' ')}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
