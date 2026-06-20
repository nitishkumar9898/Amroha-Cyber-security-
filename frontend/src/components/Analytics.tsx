import { useState, useEffect } from 'react';
import { NetworkChart } from './NetworkChart';
import { RadarChart } from './RadarChart';
import { BarChart } from './BarChart';

export const Analytics = () => {
  const [searchQuery, setSearchQuery] = useState('APT-Shadow-Agent-01');
  const [graphActor, setGraphActor] = useState('APT-Shadow-Agent-01');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [graphData, setGraphData] = useState<any>(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const token = localStorage.getItem('token');

  // Trigger search on mount and change
  const handleSearch = async () => {
    if (!searchQuery) return;
    setLoadingSearch(true);
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/forensics/search?query=${encodeURIComponent(searchQuery)}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data);
      } else {
        setSearchResults([{ error: 'Failed to query search index. Auth required?' }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSearch(false);
    }
  };

  const fetchGraph = async () => {
    if (!graphActor) return;
    setLoadingGraph(true);
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/forensics/graph?actor_name=${encodeURIComponent(graphActor)}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      } else {
        setGraphData(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingGraph(false);
    }
  };

  useEffect(() => {
    handleSearch();
    fetchGraph();
  }, [graphActor]);

  return (
    <section className="animate-in" style={{ padding: '24px 0' }}>
      <div className="dashboard-header">
        <h1 className="section-title">
          <span className="icon">🌐</span>
          <span className="text-gradient">Threat Intelligence Map & Analytics</span>
        </h1>
        <p className="section-subtitle">Query our mock Elasticsearch threat registry index and explore relational threat graph networks.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* GRAPH VIEW */}
        <div className="panel" style={{ minHeight: '420px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>Threat Actor Connection Graph</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                className="form-input" 
                value={graphActor} 
                onChange={(e) => setGraphActor(e.target.value)} 
                style={{ width: '180px', fontSize: '0.8rem', padding: '6px 10px' }}
                placeholder="Actor Name"
              />
              <button className="btn btn-primary btn-sm" onClick={fetchGraph} disabled={loadingGraph}>
                Query Map
              </button>
            </div>
          </div>

          <div style={{ flexGrow: 1, border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden', minHeight: '320px', background: '#070a13' }}>
            {loadingGraph ? (
              <div className="loading-spinner" style={{ height: '320px' }}>
                <div className="spinner"></div>
                <span>Resolving threat network vertices...</span>
              </div>
            ) : (
              <NetworkChart graphData={graphData} />
            )}
          </div>
        </div>

        {/* LOG INDEX SEARCH */}
        <div className="panel" style={{ height: '100%', minHeight: '420px', display: 'flex', flexDirection: 'column' }}>
          <h3>Search Threat Index Logs</h3>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', marginTop: '8px' }}>
            <input 
              type="text" 
              className="form-input" 
              value={searchQuery} 
              onChange={(e) => setSearchQuery(e.target.value)} 
              placeholder="Search keyword (e.g. shadow, cert)..."
              style={{ fontSize: '0.8rem' }}
            />
            <button className="btn btn-primary btn-sm" onClick={handleSearch} disabled={loadingSearch}>
              Search
            </button>
          </div>

          <div style={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {loadingSearch && (
              <div className="loading-spinner">
                <div className="spinner"></div>
                <span>Searching Elasticsearch indices...</span>
              </div>
            )}

            {!loadingSearch && searchResults.length === 0 && (
              <div className="empty-state">
                <p>No index matches found.</p>
              </div>
            )}

            {!loadingSearch && searchResults.map((doc, idx) => (
              <div 
                key={idx} 
                style={{ 
                  padding: '14px', 
                  background: 'var(--bg-secondary)', 
                  border: '1px solid var(--border)', 
                  borderRadius: '6px' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-purple)' }}>{doc.source}</span>
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>Match {Math.round(doc.relevance * 100)}%</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>{doc.content}</p>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* ADDITIONAL CHARTS & EXPLANATION */}
      <div className="chart-grid" style={{ marginTop: '24px' }}>
        <div className="chart-card">
          <h3>
            <span className="dot"></span>
            Forensic Signature Distribution
          </h3>
          <RadarChart />
        </div>
        <div className="chart-card">
          <h3>
            <span className="dot"></span>
            Intrusion Time Sequence (Trend)
          </h3>
          <BarChart />
        </div>
      </div>
    </section>
  );
};
