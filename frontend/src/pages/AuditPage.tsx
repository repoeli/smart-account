import React, { useEffect, useState } from 'react';

type AuditItem = {
  at: string;
  type: string;
  receipt_id?: string;
  data?: any;
};

const AuditPage: React.FC = () => {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [eventType, setEventType] = useState<string>('');
  const [receiptId, setReceiptId] = useState<string>('');
  const [limit, setLimit] = useState<number>(20);

  const load = async () => {
    try {
      setLoading(true);
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const url = new URL(`${apiBase}/audit/logs/`);
      if (eventType) url.searchParams.set('eventType', eventType);
      if (receiptId) url.searchParams.set('receipt_id', receiptId);
      if (limit) url.searchParams.set('limit', String(limit));
      const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
      const data = await res.json();
      if (!res.ok || !data?.success) throw new Error(data?.message || 'Failed to load audit logs');
      setItems(Array.isArray(data.items) ? data.items : []);
      setError(null);
    } catch (e: any) {
      setError(e?.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Audit Logs</h1>

      <div className="card p-4 mb-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Event type</label>
            <select value={eventType} onChange={(e)=>setEventType(e.target.value)} className="input input-bordered w-full">
              <option value="">All</option>
              <option value="receipt_validate">receipt_validate</option>
              <option value="receipt_reprocess">receipt_reprocess</option>
              <option value="receipt_replace">receipt_replace</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Receipt ID</label>
            <input value={receiptId} onChange={(e)=>setReceiptId(e.target.value)} className="input input-bordered w-full" placeholder="optional" />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Limit</label>
            <select value={limit} onChange={(e)=>setLimit(Number(e.target.value)||20)} className="input input-bordered w-full">
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn btn-primary w-full" onClick={load}>Refresh</button>
          </div>
        </div>
      </div>

      <div className="card p-4">
        {loading ? (
          <div className="py-8 text-center">Loading…</div>
        ) : error ? (
          <div className="py-8 text-center text-red-600">{error}</div>
        ) : items.length === 0 ? (
          <div className="py-8 text-center text-gray-500">No audit entries</div>
        ) : (
          <table className="w-full text-sm" aria-label="Audit logs">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Time</th>
                <th className="py-2">Event</th>
                <th className="py-2">Receipt</th>
                <th className="py-2">Details</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, idx) => (
                <tr key={idx} className="border-b last:border-0">
                  <td className="py-2">{new Date(it.at).toLocaleString()}</td>
                  <td className="py-2">{it.type}</td>
                  <td className="py-2">{it.receipt_id || '-'}</td>
                  <td className="py-2"><pre className="whitespace-pre-wrap text-xs text-gray-600">{JSON.stringify(it.data || {}, null, 2)}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AuditPage;


