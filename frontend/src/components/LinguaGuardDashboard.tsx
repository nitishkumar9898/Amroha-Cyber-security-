import React, { useState, useEffect } from "react";
import axios from "axios";
import "./LinguaGuardDashboard.css";

export const LinguaGuardDashboard: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [language, setLanguage] = useState("");
  const [originalText, setOriginalText] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = () => {
    axios.get("/api/linguaguard/tasks").then(res => setTasks(res.data)).catch(console.error);
  };

  const handleTranslate = () => {
    setIsTranslating(true);
    axios.post("/api/linguaguard/translate", { source_language: language, original_text: originalText })
      .then(() => {
        fetchTasks();
        setLanguage(""); setOriginalText("");
      })
      .catch(console.error)
      .finally(() => setIsTranslating(false));
  };

  return (
    <div className="lg-container">
      <h2>LinguaGuard Dashboard</h2>
      
      <div className="lg-card">
        <h3>Multilingual Threat Translation</h3>
        <input placeholder="Source Language (e.g., Russian, Mandarin)" value={language} onChange={e => setLanguage(e.target.value)} />
        <textarea placeholder="Paste intercepted text here..." value={originalText} onChange={e => setOriginalText(e.target.value)} />
        <button onClick={handleTranslate} disabled={isTranslating}>{isTranslating ? "Processing..." : "Translate & Analyze"}</button>
      </div>

      <div className="lg-card">
        <h3>Translation Log</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Language</th>
              <th>Original</th>
              <th>Translated Text</th>
              <th>Intent Score</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(task => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>{task.source_language}</td>
                <td>{task.original_text.substring(0, 30)}...</td>
                <td>{task.translated_text}</td>
                <td className={task.threat_intent_score > 0.7 ? "high-intent" : ""}>{(task.threat_intent_score * 100).toFixed(1)}%</td>
                <td>{new Date(task.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
