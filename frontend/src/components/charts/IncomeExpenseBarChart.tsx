import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import Shimmer from './Shimmer';

interface IncomeExpenseSummary {
  income: string;
  expense: string;
  start_date: string;
  end_date: string;
}

const IncomeExpenseBarChart: React.FC = () => {
  const [data, setData] = useState<IncomeExpenseSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - days);

        const params = {
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
        };

        const response = await api.getIncomeExpenseSummary(params);
        if (response.success) {
          setData(response.summary);
        } else {
          setError('Failed to fetch income/expense summary.');
        }
      } catch (err) {
        setError('An error occurred while fetching data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [days]);

  if (loading) {
    return <Shimmer />;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  if (!data) {
    return null;
  }

  const income = parseFloat(data.income);
  const expense = parseFloat(data.expense);
  const max = Math.max(income, expense, 1); // Avoid division by zero

  const incomeHeight = (income / max) * 100;
  const expenseHeight = (expense / max) * 100;

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold">Income vs. Expense</h3>
        <div>
          <button onClick={() => setDays(30)} className={`px-2 py-1 text-sm ${days === 30 ? 'bg-blue-500 text-white' : ''}`}>30d</button>
          <button onClick={() => setDays(90)} className={`px-2 py-1 text-sm ${days === 90 ? 'bg-blue-500 text-white' : ''}`}>90d</button>
          <button onClick={() => setDays(365)} className={`px-2 py-1 text-sm ${days === 365 ? 'bg-blue-500 text-white' : ''}`}>1y</button>
        </div>
      </div>
      <div className="flex justify-around items-end h-64">
        <div className="flex flex-col items-center">
          <div className="w-16 bg-green-400" style={{ height: `${incomeHeight}%` }}></div>
          <span className="text-sm">Income</span>
          <span className="font-semibold">£{income.toFixed(2)}</span>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-16 bg-red-400" style={{ height: `${expenseHeight}%` }}></div>
          <span className="text-sm">Expense</span>
          <span className="font-semibold">£{expense.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

export default IncomeExpenseBarChart;
