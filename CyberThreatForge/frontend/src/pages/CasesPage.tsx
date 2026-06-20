import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, FolderSearch, Shield, Clock, User, MoreVertical } from 'lucide-react';
import api from '../services/api';

interface Case {
  id: string;
  title: string;
  description: string;
  classification: string;
  type: string;
  status: string;
  jurisdiction: string;
  fir_number: string | null;
  created_by: string;
  assigned_to: string | null;
  created_at: string;
  evidence_count?: number;
}

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-green-900/50 text-green-400',
  under_investigation: 'bg-blue-900/50 text-blue-400',
  closed: 'bg-gray-800 text-gray-400',
  archived: 'bg-gray-800/50 text-gray-600',
};

const CLASS_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-900/50 text-red-400',
  HIGH: 'bg-amber-900/50 text-amber-400',
  MEDIUM: 'bg-blue-900/50 text-blue-400',
  LOW: 'bg-gray-800 text-gray-400',
};

export function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await api.get('/cases');
        setCases(data ?? []);
      } catch { /* */ }
      setLoading(false);
    };
    fetch();
  }, []);

  const filtered = cases.filter((c) => {
    const matchesSearch = c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.fir_number?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Cases</h1>
          <p className="text-sm text-gray-500">{cases.length} total cases</p>
        </div>
        <Link
          to="/cases/new"
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg text-sm hover:bg-cyan-500 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Case
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by title or FIR number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-cyan-600"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          {['all', 'open', 'under_investigation', 'closed', 'archived'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded text-xs transition-colors ${
                statusFilter === s
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-600">Loading cases...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-600">
          <FolderSearch className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No cases found</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filtered.map((c) => (
            <Link
              key={c.id}
              to={`/cases/${c.id}`}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-gray-200 truncate">{c.title}</h3>
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[c.status] ?? ''}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${CLASS_COLORS[c.classification] ?? ''}`}>
                      {c.classification}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-1 mb-2">{c.description}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      {c.jurisdiction}
                    </span>
                    {c.fir_number && (
                      <span className="flex items-center gap-1">
                        FIR: {c.fir_number}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {c.created_by?.slice(0, 8)}...
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <button className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-gray-300 transition-all">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
