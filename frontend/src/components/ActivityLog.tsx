import { useState, useEffect } from 'react';

interface LogEntry {
  timestamp: string;
  level: string;
  category: string;
  message: string;
}

export const ActivityLog = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const token = localStorage.getItem('token');

  const fetchLogs = async () => {
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/activity/log', { headers });
      if (res.status === 401) {
        setLogs([{ timestamp: '--:--:--', level: 'ALERT', category: 'AUTH', message: 'Unauthorized. Log in inside the Admin tab to view live system logs.' }]);
        setLoading(false);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  // Set up auto refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchLogs, 8000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Handle filtering
  useEffect(() => {
    let result = [...logs];

    if (levelFilter !== 'ALL') {
      result = result.filter(log => log.level === levelFilter);
    }

    if (search) {
      result = result.filter(log => 
        log.message.toLowerCase().includes(search.toLowerCase()) || 
        log.category.toLowerCase().includes(search.toLowerCase())
      );
    }

    setFilteredLogs(result);
  }, [logs, search, levelFilter]);

  const getLevelBadgeClass = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ALERT': return 'badge-alert';
      case 'WARNING': return 'badge-warning';
      case 'SUCCESS': return 'badge-success';
      case 'INFO': return 'badge-info';
      default: return 'badge-info';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toUpperCase()) {
      case 'AUTH': return '🔑';
      case 'SIMULATION': return '🎮';
      case 'DEEPFAKE': return '📹';
      case 'MALWARE': return '☣️';
      case 'MOBILE': return '📱';
      case 'DARKWEB': return '🧅';
      case 'AUDIT': return '🔒';
      case 'TAMPER': return '💥';
      case 'CERTIFY': return '📜';
      case 'HARDWARE': return '🔌';
      case 'PSYCHOLOGY': return '🧠';
      case 'MISINFO': return '📢';
      default: return '📡';
    }
  };

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header">
        <h1 className="section-title">
          <span className="icon">📡</span>
          <span className="text-gradient">Real-Time Threat Activity Stream</span>
        </h1>
        <p className="section-subtitle">Monitor ongoing simulated sandbox and forensic decodes on this local network node.</p>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexGrow: 1, maxWidth: '600px' }}>
            <input 
              type="text" 
              className="form-input" 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
              placeholder="Search stream message or category..."
              style={{ fontSize: '0.8rem' }}
            />
            <select 
              className="form-select" 
              value={levelFilter} 
              onChange={(e) => setLevelFilter(e.target.value)}
              style={{ width: '150px', fontSize: '0.8rem' }}
            >
              <option value="ALL">All Levels</option>
              <option value="INFO">INFO</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="WARNING">WARNING</option>
              <option value="ALERT">ALERT</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input 
                type="checkbox" 
                checked={autoRefresh} 
                onChange={(e) => setAutoRefresh(e.target.checked)} 
              />
              Auto-stream (8s)
            </label>
            <button className="btn btn-outline btn-sm" onClick={fetchLogs} disabled={loading}>
              🔄 Refresh
            </button>
          </div>

        </div>

        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Interpreting live audit records...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="empty-state">
            <p>No activity logs found matching the selected filter criteria.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>Timestamp</th>
                  <th style={{ width: '120px' }}>Severity</th>
                  <th style={{ width: '140px' }}>Channel</th>
                  <th>Incident Log Message</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.05)' }}>
                    <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{log.timestamp}</td>
                    <td>
                      <span className={`badge ${getLevelBadgeClass(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                      <span style={{ marginRight: '6px' }}>{getCategoryIcon(log.category)}</span>
                      {log.category}
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
};
