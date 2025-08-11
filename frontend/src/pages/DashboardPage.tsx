import { useAppSelector } from '../store';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

type Totals = { income: { currency: string; sum: string }[]; expense: { currency: string; sum: string }[] };

const formatMoney = (amount: string | number, currency: string) => {
  const value = typeof amount === 'number' ? amount : Number(amount);
  if (Number.isNaN(value)) return `${currency} ${amount}`;
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value); } catch { return `${currency} ${value.toFixed(2)}`; }
};

const DashboardPage = () => {
  const { user } = useAppSelector((state) => state.auth);
  const [totals, setTotals] = useState<Totals>({ income: [], expense: [] });
  const [receiptsCount, setReceiptsCount] = useState<number>(0);
  const [range, setRange] = useState<'this_month' | 'last_month' | 'this_year' | 'custom'>('this_month');
  // removed unused loading state to avoid linter warning
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [byMonthRaw, setByMonthRaw] = useState<Array<{month:string;currency:string;income:number;expense:number}>>([]);
  const [byCategoryRaw, setByCategoryRaw] = useState<Array<{category:string;currency:string;income:number;expense:number}>>([]);
  const [byMerchantRaw, setByMerchantRaw] = useState<Array<{merchant:string;currency:string;income:number;expense:number}>>([]);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Hydrate persisted range and dates
  useEffect(() => {
    try {
      const raw = localStorage.getItem('dashboard_range');
      if (raw) {
        const saved = JSON.parse(raw);
        if (saved.range) setRange(saved.range);
        if (saved.dateFrom) setDateFrom(saved.dateFrom);
        if (saved.dateTo) setDateTo(saved.dateTo);
      }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist range and dates
  useEffect(() => {
    try {
      localStorage.setItem('dashboard_range', JSON.stringify({ range, dateFrom, dateTo }));
    } catch {}
  }, [range, dateFrom, dateTo]);

  useEffect(() => {
    (async () => {
      try {
        const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
        const now = new Date();
        let df = dateFrom;
        let dt = dateTo;
        if (range !== 'custom') {
          let start: Date;
          let end: Date;
          if (range === 'last_month') {
            const first = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            const last = new Date(now.getFullYear(), now.getMonth(), 0);
            start = first; end = last;
          } else if (range === 'this_year') {
            start = new Date(now.getFullYear(), 0, 1);
            end = new Date(now.getFullYear(), 11, 31);
          } else {
            start = new Date(now.getFullYear(), now.getMonth(), 1);
            end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
          }
          df = start.toISOString().slice(0, 10);
          dt = end.toISOString().slice(0, 10);
          setDateFrom(df);
          setDateTo(dt);
        } else {
          if (!df || !dt) return;
        }
        const url = new URL(`${apiBase}/transactions/summary/`);
        url.searchParams.set('dateFrom', df);
        url.searchParams.set('dateTo', dt);
        url.searchParams.set('groupBy', 'month,category,merchant');
        const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
        if (!res.ok) {
          setSummaryError('Failed to load summary');
          setTotals({ income: [], expense: [] });
          setByMonthRaw([]);
          setByCategoryRaw([]);
          setByMerchantRaw([]);
        } else {
          const data = await res.json().catch(() => ({}));
          if (data?.success && data.totals) setTotals(data.totals);
          if (data?.success) {
            setByMonthRaw(Array.isArray(data.byMonth) ? data.byMonth : []);
            setByCategoryRaw(Array.isArray(data.byCategory) ? data.byCategory : []);
            setByMerchantRaw(Array.isArray(data.byMerchant) ? data.byMerchant : []);
            setSummaryError(null);
          }
        }

        // Fetch total receipts count via lightweight endpoint
        try {
          const recUrl = new URL(`${apiBase}/receipts/count/`);
          const rres = await fetch(recUrl.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
          const rdata = await rres.json();
          if (rres.ok && rdata?.success && typeof rdata?.count === 'number') {
            setReceiptsCount(rdata.count);
          }
        } catch {}
      } finally {
      }
    })();
  }, [range, dateFrom, dateTo]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {summaryError && (
        <div className="mb-4 p-3 border border-yellow-200 bg-yellow-50 text-yellow-700 rounded">
          {summaryError}
        </div>
      )}
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="text-gray-600">
          Here's what's happening with your receipts today.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-600">Date Range</div>
        <div className="flex gap-2">
          <button className={`btn btn-outline ${range==='this_month'?'btn-active':''}`} onClick={() => setRange('this_month')}>This month</button>
          <button className={`btn btn-outline ${range==='last_month'?'btn-active':''}`} onClick={() => setRange('last_month')}>Last month</button>
          <button className={`btn btn-outline ${range==='this_year'?'btn-active':''}`} onClick={() => setRange('this_year')}>This year</button>
          <button className={`btn btn-outline ${range==='custom'?'btn-active':''}`} onClick={() => setRange('custom')}>Custom</button>
        </div>
      </div>
      {range === 'custom' && (
        <div className="mb-6 flex items-center gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">From</label>
            <input type="date" value={dateFrom} onChange={(e)=>setDateFrom(e.target.value)} className="input input-bordered" />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">To</label>
            <input type="date" value={dateTo} onChange={(e)=>setDateTo(e.target.value)} className="input input-bordered" />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card cursor-pointer" onClick={() => navigate(`/transactions?dateFrom=${dateFrom}&dateTo=${dateTo}`)}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">📄</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Receipts</h3>
              <p className="text-2xl font-semibold text-gray-900">{receiptsCount}</p>
            </div>
          </div>
        </div>

        <div className="card cursor-pointer" onClick={() => navigate(`/transactions?dateFrom=${dateFrom}&dateTo=${dateTo}&type=income`)}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">💰</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Income</h3>
              <p className="text-2xl font-semibold text-gray-900">
                {totals.income.length
                  ? totals.income.map(t => <span key={`inc-${t.currency}`} className="mr-2">{formatMoney(t.sum, t.currency)}</span>)
                  : formatMoney(0, 'GBP')}
              </p>
            </div>
          </div>
        </div>

        <div className="card cursor-pointer" onClick={() => navigate(`/transactions?dateFrom=${dateFrom}&dateTo=${dateTo}&type=expense`)}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Expenses</h3>
              <p className="text-2xl font-semibold text-gray-900">
                {totals.expense.length
                  ? totals.expense.map(t => <span key={`exp-${t.currency}`} className="mr-2">{formatMoney(t.sum, t.currency)}</span>)
                  : formatMoney(0, 'GBP')}
              </p>
            </div>
          </div>
        </div>

        <div className="card cursor-pointer" onClick={() => navigate(`/transactions?dateFrom=${dateFrom}&dateTo=${dateTo}`)}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">🏢</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Net (Income - Expenses)</h3>
              <p className="text-2xl font-semibold text-gray-900">
                {(() => {
                  // Compute net only for currencies present in both sets
                  const curSet = new Set<string>([...totals.income.map(i => i.currency), ...totals.expense.map(e => e.currency)]);
                  const parts: React.ReactNode[] = [];
                  curSet.forEach(cur => {
                    const inc = Number(totals.income.find(i => i.currency === cur)?.sum || 0);
                    const exp = Number(totals.expense.find(e => e.currency === cur)?.sum || 0);
                    parts.push(<span key={`net-${cur}`} className="mr-2">{formatMoney(inc - exp, cur)}</span>);
                  });
                  return parts.length ? parts : formatMoney(0, 'GBP');
                })()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Simple charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-4">
          <h3 className="font-semibold mb-3">Income vs Expense by Month</h3>
          <div className="space-y-2">
            {(() => {
              const acc: Record<string, { income: number; expense: number }> = {};
              byMonthRaw.forEach(r => {
                acc[r.month] = acc[r.month] || { income: 0, expense: 0 };
                acc[r.month].income += r.income;
                acc[r.month].expense += r.expense;
              });
              const rows = Object.entries(acc).sort((a,b)=>a[0].localeCompare(b[0]));
              const maxVal = rows.reduce((m, [,v])=>Math.max(m, v.income, v.expense), 0) || 1;
              return rows.map(([m, v]) => (
                <div key={m} className="text-xs">
                  <div className="flex justify-between mb-1"><span>{m}</span><span>{formatMoney(v.income - v.expense, 'GBP')}</span></div>
                  <div className="h-3 bg-gray-100 rounded">
                    <div className="h-3 bg-green-500 rounded-l inline-block" style={{width: `${(v.income/maxVal)*100}%`}} title={`Income ${v.income.toFixed(2)}`}></div>
                    <div className="h-3 bg-yellow-500 inline-block" style={{width: `${(v.expense/maxVal)*100}%`}} title={`Expense ${v.expense.toFixed(2)}`}></div>
                  </div>
                </div>
              ));
            })()}
          </div>
        </div>
        <div className="card p-4">
          <h3 className="font-semibold mb-3">Category Breakdown</h3>
          <div className="space-y-2">
            {(() => {
              const acc: Record<string, { total: number }> = {};
              byCategoryRaw.forEach(r => {
                const key = r.category || 'uncategorized';
                acc[key] = acc[key] || { total: 0 };
                acc[key].total += r.income + r.expense;
              });
              const rows = Object.entries(acc).sort((a,b)=>b[1].total - a[1].total).slice(0,8);
              const maxVal = rows.reduce((m, [,v])=>Math.max(m, v.total), 1);
              return rows.map(([cat, v]) => (
                <div key={cat} className="text-xs">
                  <div className="flex justify-between mb-1"><span>{cat}</span><span>{formatMoney(v.total, 'GBP')}</span></div>
                  <div className="h-3 bg-gray-100 rounded">
                    <div className="h-3 bg-blue-500 rounded" style={{width: `${(v.total/maxVal)*100}%`}}></div>
                  </div>
                </div>
              ));
            })()}
          </div>
        </div>
        <div className="card p-4 lg:col-span-2">
          <h3 className="font-semibold mb-3">Top Merchants</h3>
          <div className="space-y-2">
            {(() => {
              const acc: Record<string, { total: number }> = {};
              byMerchantRaw.forEach(r => {
                const key = r.merchant || 'unknown';
                acc[key] = acc[key] || { total: 0 };
                acc[key].total += r.income + r.expense;
              });
              const rows = Object.entries(acc).sort((a,b)=>b[1].total - a[1].total).slice(0,10);
              const maxVal = rows.reduce((m, [,v])=>Math.max(m, v.total), 1);
              return rows.map(([merch, v]) => (
                <div key={merch} className="text-xs">
                  <div className="flex justify-between mb-1"><span>{merch || 'Unknown'}</span><span>{formatMoney(v.total, 'GBP')}</span></div>
                  <div className="h-3 bg-gray-100 rounded">
                    <div className="h-3 bg-indigo-500 rounded" style={{width: `${(v.total/maxVal)*100}%`}}></div>
                  </div>
                </div>
              ));
            })()}
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Getting Started</h3>
          <div className="space-y-3">
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0 h-6 w-6 bg-primary-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-primary-600 text-sm font-medium">1</span>
              </div>
              <span className="text-sm text-gray-700">Upload your first receipt</span>
            </div>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0 h-6 w-6 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                <span className="text-gray-500 text-sm font-medium">2</span>
              </div>
              <span className="text-sm text-gray-500">Create folders for organization</span>
            </div>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0 h-6 w-6 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                <span className="text-gray-500 text-sm font-medium">3</span>
              </div>
              <span className="text-sm text-gray-500">Set up categories and tags</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="text-center py-8">
            <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📭</span>
            </div>
            <p className="text-gray-500">No recent activity</p>
            <p className="text-sm text-gray-400 mt-1">
              Start by uploading your first receipt
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 text-center">
        <div className="card inline-block">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="flex space-x-4">
            <button className="btn-primary">
              📤 Upload Receipt
            </button>
            <button className="btn-secondary">
              📁 Create Folder
            </button>
            <button className="btn-secondary">
              🔍 Search Receipts
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;