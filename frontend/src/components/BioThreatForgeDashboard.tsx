import React, { useEffect, useState } from 'react';
import { fetchAnalysis } from '../services/biothreatforge';
import styles from './BioThreatForgeDashboard.module.css';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface AnalysisResult {
  sequence_id: string;
  bioweapon_probability: number;
  source_facility: string;
  timestamp: string;
}

const BioThreatForgeDashboard: React.FC = () => {
  const [data, setData] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchAnalysis()
      .then((res: any) => {
        setData(res);
        setLoading(false);
      })
      .catch((_err: any) => {
        setError('Failed to load analysis data');
        setLoading(false);
      });
  }, []);

  const summary = {
    totalSequences: data.length,
    highestThreat: data.reduce((max, cur) => (cur.bioweapon_probability > max ? cur.bioweapon_probability : max), 0),
  };

  return (
    <div className={styles.dashboardWrapper}>
      <h2 className={styles.title}>BioThreatForge Dashboard</h2>
      {loading && <p>Loading...</p>}
      {error && <p className={styles.error}>{error}</p>}
      {!loading && !error && (
        <>
          <div className={styles.summaryCard}>
            <h3>Summary</h3>
            <p>Total Sequences Processed: {summary.totalSequences}</p>
            <p>Highest Threat Probability: {summary.highestThreat.toFixed(2)}%</p>
          </div>
          <div className={styles.tableContainer}>
            <h3>Recent Analyses</h3>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Sequence ID</th>
                  <th>Facility</th>
                  <th>Threat %</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {data.slice(0, 10).map((row) => (
                  <tr key={row.sequence_id} className={styles.tableRow}>
                    <td>{row.sequence_id}</td>
                    <td>{row.source_facility}</td>
                    <td>{row.bioweapon_probability.toFixed(2)}%</td>
                    <td>{new Date(row.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.chartContainer}>
            <h3>Threat Probability Heatmap</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data}>
                <XAxis dataKey="sequence_id" hide={true} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="bioweapon_probability" fill="var(--primary)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
};

export default BioThreatForgeDashboard;
