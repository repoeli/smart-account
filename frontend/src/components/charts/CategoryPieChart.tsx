import React, { useEffect, useState } from 'react';
import { apiClient } from '../../services/api';
import Shimmer from './Shimmer';

interface CategorySummary {
  category: string;
  total_amount: string;
  transaction_count: number;
}

const CategoryPieChart: React.FC = () => {
  const [data, setData] = useState<CategorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.getCategorySummary();
        if (response.success) {
          setData(response.summary);
        } else {
          setError('Failed to fetch category summary.');
        }
      } catch (err) {
        setError('An error occurred while fetching data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <Shimmer />;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  const total = data.reduce((acc, item) => acc + parseFloat(item.total_amount), 0);

  const colors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
  ];

  let cumulativePercent = 0;
  const paths = data.map((item, index) => {
    const percent = parseFloat(item.total_amount) / total;
    const startAngle = cumulativePercent * 360;
    const endAngle = (cumulativePercent + percent) * 360;
    cumulativePercent += percent;

    const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
    
    const x1 = 50 + 40 * Math.cos(Math.PI * (startAngle - 90) / 180);
    const y1 = 50 + 40 * Math.sin(Math.PI * (startAngle - 90) / 180);
    const x2 = 50 + 40 * Math.cos(Math.PI * (endAngle - 90) / 180);
    const y2 = 50 + 40 * Math.sin(Math.PI * (endAngle - 90) / 180);

    return (
      <path
        key={item.category}
        d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
        fill={colors[index % colors.length]}
      />
    );
  });

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-2">Expenses by Category</h3>
      <div className="flex">
        <svg viewBox="0 0 100 100" className="w-48 h-48">
          {paths}
        </svg>
        <div className="ml-4 flex-grow">
          <ul>
            {data.map((item, index) => (
              <li key={item.category} className="flex items-center mb-1">
                <span className="w-4 h-4 mr-2" style={{ backgroundColor: colors[index % colors.length] }}></span>
                <span>{item.category || 'Uncategorized'}: £{parseFloat(item.total_amount).toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CategoryPieChart;
