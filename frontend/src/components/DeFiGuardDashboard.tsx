import React, { useState, useEffect } from "react";
import axios from "axios";
import "./DeFiGuardDashboard.css";

export const DeFiGuardDashboard: React.FC = () => {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [wallet, setWallet] = useState("");
  const [txHash, setTxHash] = useState("");
  const [trace, setTrace] = useState<any>(null);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = () => {
    axios.get("/api/defiguard/transactions").then(res => setTransactions(res.data)).catch(console.error);
  };

  const handleAnalyze = () => {
    axios.post("/api/defiguard/analyze", { wallet_address: wallet, transaction_hash: txHash })
      .then(() => {
        fetchTransactions();
        setWallet(""); setTxHash("");
      })
      .catch(console.error);
  };

  const handleTrace = (hash: string) => {
    axios.get(`/api/defiguard/trace/${hash}`)
      .then(res => setTrace(res.data))
      .catch(console.error);
  };

  return (
    <div className="dg-container">
      <h2>DeFiGuard Dashboard</h2>
      
      <div className="dg-card">
        <h3>Analyze Blockchain Transaction</h3>
        <input placeholder="Wallet Address (0x...)" value={wallet} onChange={e => setWallet(e.target.value)} />
        <input placeholder="Transaction Hash (0x...)" value={txHash} onChange={e => setTxHash(e.target.value)} />
        <button onClick={handleAnalyze}>Analyze Risk</button>
      </div>

      {trace && (
        <div className="dg-card dg-trace">
          <h3>Transaction Trace Map ({trace.transaction_hash})</h3>
          <p><strong>Hops Analyzed:</strong> {trace.hops}</p>
          <p><strong>Associated Entities:</strong> {trace.associated_entities}</p>
          <button onClick={() => setTrace(null)}>Close Trace</button>
        </div>
      )}

      <div className="dg-card">
        <h3>Monitored Transactions</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Wallet Address</th>
              <th>Tx Hash</th>
              <th>Risk Score</th>
              <th>Flags</th>
              <th>Time</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map(tx => (
              <tr key={tx.id}>
                <td>{tx.id}</td>
                <td>{tx.wallet_address.substring(0, 10)}...</td>
                <td>{tx.transaction_hash.substring(0, 10)}...</td>
                <td className={tx.risk_score > 0.7 ? "high-risk" : ""}>{(tx.risk_score * 100).toFixed(1)}%</td>
                <td>{tx.flags}</td>
                <td>{new Date(tx.analyzed_at).toLocaleString()}</td>
                <td>
                  <button className="trace-btn" onClick={() => handleTrace(tx.transaction_hash)}>Deep Trace</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
