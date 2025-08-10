import React, { useEffect, useState } from 'react';
// import { apiClient } from '../services/api';

interface TxItem {
  id: string;
  transaction_date: string;
  description: string;
  merchant?: string | null;
  type: 'income' | 'expense';
  amount: string;
  currency: string;
  category?: string | null;
}

const TransactionsPage: React.FC = () => {
  const [items, setItems] = useState<TxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res: any = await fetch(`${(import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/transactions/?limit=50&offset=0`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
          }
        });
        const data = await res.json();
        if (res.ok && data?.success) setItems(data.items || []);
        else setError(data?.message || 'Failed to load transactions');
      } catch (e: any) {
        setError(e?.message || 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading…</div></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-6">Transactions</h1>
      <div className="card p-4">
        {items.length === 0 ? (
          <div className="text-center text-gray-500">No transactions yet.</div>
        ) : (
          <table className="w-full text-sm" aria-label="Transactions list">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Date</th>
                <th className="py-2">Merchant</th>
                <th className="py-2">Description</th>
                <th className="py-2">Type</th>
                <th className="py-2 text-right">Amount</th>
                <th className="py-2">Category</th>
              </tr>
            </thead>
            <tbody>
              {items.map(tx => (
                <tr key={tx.id} className="border-b last:border-0">
                  <td className="py-2">{new Date(tx.transaction_date).toLocaleDateString()}</td>
                  <td className="py-2">{tx.merchant || '-'}</td>
                  <td className="py-2">{tx.description}</td>
                  <td className="py-2">{tx.type}</td>
                  <td className="py-2 text-right">{tx.currency} {tx.amount}</td>
                  <td className="py-2">{tx.category || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TransactionsPage;

