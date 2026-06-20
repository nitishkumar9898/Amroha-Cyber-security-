import React from 'react';
import './training.css';

interface PerformanceHUDProps {
  score?: number;
  timeElapsed?: number; // seconds
  hintsUsed?: number;
}

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const PerformanceHUD: React.FC<PerformanceHUDProps> = ({ score = 0, timeElapsed = 0, hintsUsed = 0 }) => {
  return (
    <div className="performance-hud glassmorphic">
      <div className="hud-item">
        <span className="hud-label">Score</span>
        <span className="hud-value">{score}</span>
      </div>
      <div className="hud-item">
        <span className="hud-label">Time</span>
        <span className="hud-value">{formatTime(timeElapsed)}</span>
      </div>
      <div className="hud-item">
        <span className="hud-label">Hints</span>
        <span className="hud-value">{hintsUsed}</span>
      </div>
    </div>
  );
};

export default PerformanceHUD;
