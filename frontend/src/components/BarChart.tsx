import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
);

interface BarChartProps {
  trendData?: Array<{ hour: string; count: number }>;
}

export const BarChart = ({ trendData }: BarChartProps) => {
  const labels = trendData ? trendData.map(d => d.hour) : ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00'];
  const values = trendData ? trendData.map(d => d.count) : [2, 4, 1, 5, 3, 4];

  const data = {
    labels,
    datasets: [
      {
        label: 'Threat Incidents',
        data: values,
        backgroundColor: 'rgba(139, 92, 246, 0.4)',
        borderColor: '#8b5cf6',
        borderWidth: 1.5,
        borderRadius: 4,
        hoverBackgroundColor: 'rgba(139, 92, 246, 0.7)',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(56, 189, 248, 0.05)',
        },
        ticks: {
          color: '#94a3b8',
          font: {
            family: 'JetBrains Mono',
            size: 10,
          },
        },
      },
      y: {
        grid: {
          color: 'rgba(56, 189, 248, 0.08)',
        },
        ticks: {
          color: '#94a3b8',
          stepSize: 1,
          font: {
            family: 'JetBrains Mono',
            size: 10,
          },
        },
      },
    },
  };

  return (
    <div style={{ height: '280px', position: 'relative' }}>
      <Bar data={data} options={options} />
    </div>
  );
};
