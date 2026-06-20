import React from 'react';
import './BioThreatForgeChart.css';

interface ChartProps {
  label: string;
  value: number; // 0 to 1
  color?: string;
}

export const BioThreatForgeChart: React.FC<ChartProps> = ({ label, value, color = '#00ffd5' }) => {
  const percentage = Math.round(value * 100);
  return (
    <div className="btf-chart">
      <div className="btf-chart-label">{label}</div>
      <svg viewBox="0 0 100 10" className="btf-chart-svg">
        <rect x="0" y="0" width="100" height="10" fill="#444" />
        <rect x="0" y="0" width={percentage} height="10" fill={color} />
      </svg>
      <div className="btf-chart-perc">{percentage}%</div>
    </div>
  );
};

export default BioThreatForgeChart;
