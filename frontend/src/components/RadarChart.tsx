import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface RadarChartProps {
  data?: Record<string, number>;
}

export const RadarChart = ({ data }: RadarChartProps) => {
  const chartData = {
    labels: data ? Object.keys(data).map(k => k.toUpperCase()) : ['DEEPFAKE', 'MALWARE', 'MOBILE', 'DARKWEB', 'PSYCHOLOGY', 'HARDWARE'],
    datasets: [
      {
        label: 'Threat Intensity / Module Usage',
        data: data ? Object.values(data) : [8, 5, 12, 4, 6, 3],
        backgroundColor: 'rgba(6, 182, 212, 0.2)',
        borderColor: '#06b6d4',
        borderWidth: 2,
        pointBackgroundColor: '#8b5cf6',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#8b5cf6',
      },
    ],
  };

  const options = {
    scales: {
      r: {
        angleLines: {
          color: 'rgba(56, 189, 248, 0.2)',
        },
        grid: {
          color: 'rgba(56, 189, 248, 0.1)',
        },
        pointLabels: {
          color: '#94a3b8',
          font: {
            family: 'Inter',
            size: 10,
            weight: 600 as const,
          },
        },
        ticks: {
          color: '#64748b',
          backdropColor: 'transparent',
          font: {
            family: 'JetBrains Mono',
            size: 9,
          },
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <div style={{ height: '280px', position: 'relative' }}>
      <Radar data={chartData} options={options} />
    </div>
  );
};
