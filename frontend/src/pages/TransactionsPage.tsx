import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

interface TxItem {
  id: string;
  transaction_date: string;
  description: string;
  merchant?: string | null;
  type: 'income' | 'expense';
  amount: string;
  currency: string;
  category?: string | null;
  receipt_id?: string | null;
}

const formatMoney = (amount: string, currency: string) => {
  const value = Number(amount);
  if (Number.isNaN(value)) return `${currency} ${amount}`;
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value);
  } catch {
    return `${currency} ${value.toFixed(2)}`;
  }
};

const TransactionsPage: React.FC = () => {
  const [items, setItems] = useState<TxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageInfo, setPageInfo] = useState<{limit:number;offset:number;totalCount:number;hasNext:boolean;hasPrev:boolean}>({limit:50,offset:0,totalCount:0,hasNext:false,hasPrev:false});
  const [totals, setTotals] = useState<{income:{currency:string;sum:string}[];expense:{currency:string;sum:string}[]}>({income:[], expense:[]});
  const [categories, setCategories] = useState<string[]>([]);

  const [searchParams, setSearchParams] = useSearchParams();

  const sort = searchParams.get('sort') || 'date';
  const order = searchParams.get('order') || 'desc';
  const dateFrom = searchParams.get('dateFrom') || '';
  const dateTo = searchParams.get('dateTo') || '';
  const type = searchParams.get('type') || '';
  const category = searchParams.get('category') || '';
  const pageLimit = Number(searchParams.get('limit') || 50);
  const pageOffset = Number(searchParams.get('offset') || 0);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
        // fetch categories (once per page load)
        try {
          if (!categories.length) {
            const catRes = await fetch(`${apiBase}/categories/`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` }});
            if (catRes.ok) {
              const cdata = await catRes.json();
              if (cdata?.success && Array.isArray(cdata.categories)) setCategories(cdata.categories);
            }
          }
        } catch {}
        const url = new URL(`${apiBase}/transactions/`);
        const limit = pageLimit;
        const offset = pageOffset;
        url.searchParams.set('limit', String(limit));
        url.searchParams.set('offset', String(offset));
        if (sort) url.searchParams.set('sort', sort);
        if (order) url.searchParams.set('order', order);
        if (dateFrom) url.searchParams.set('dateFrom', dateFrom);
        if (dateTo) url.searchParams.set('dateTo', dateTo);
        if (type) url.searchParams.set('type', type);
        if (category) url.searchParams.set('category', category);
        const res: any = await fetch(url.toString(), {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
          }
        });
        const data = await res.json();
        if (res.ok && data?.success) {
          setItems(data.items || []);
          if (data.page) setPageInfo(data.page);
          if (data.totals) setTotals(data.totals);
        }
        else setError(data?.message || 'Failed to load transactions');
      } catch (e: any) {
        setError(e?.message || 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    })();
  }, [sort, order, dateFrom, dateTo, type, category, searchParams]);

  const setPage = (nextOffset: number) => {
    if (nextOffset < 0) return;
    searchParams.set('offset', String(nextOffset));
    searchParams.set('limit', String(pageInfo.limit));
    setSearchParams(searchParams, { replace: true });
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    searchParams.set('sort', e.target.value);
    setSearchParams(searchParams, { replace: true });
  };
  const handleOrderToggle = () => {
    searchParams.set('order', order === 'desc' ? 'asc' : 'desc');
    setSearchParams(searchParams, { replace: true });
  };
  const handlePageSize = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = Number(e.target.value) || 50;
    searchParams.set('limit', String(val));
    searchParams.set('offset', '0');
    setSearchParams(searchParams, { replace: true });
  };
  const handleDateFrom = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val) searchParams.set('dateFrom', val); else searchParams.delete('dateFrom');
    setSearchParams(searchParams, { replace: true });
  };
  const handleDateTo = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val) searchParams.set('dateTo', val); else searchParams.delete('dateTo');
    setSearchParams(searchParams, { replace: true });
  };
  const handleType = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val) searchParams.set('type', val); else searchParams.delete('type');
    setSearchParams(searchParams, { replace: true });
  };
  const handleCategory = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val) searchParams.set('category', val); else searchParams.delete('category');
    setSearchParams(searchParams, { replace: true });
  };
  const clearFilters = () => {
    ['dateFrom', 'dateTo', 'type', 'category'].forEach(k => searchParams.delete(k));
    searchParams.set('offset', '0');
    setSearchParams(searchParams, { replace: true });
  };

  // Persist filter/sort state
  useEffect(() => {
    const state = { sort, order, dateFrom, dateTo, type, category, limit: pageLimit, offset: pageOffset };
    try { localStorage.setItem('tx_filters', JSON.stringify(state)); } catch {}
  }, [sort, order, dateFrom, dateTo, type, category, pageLimit, pageOffset]);

  // Hydrate from last-used on initial mount when params are mostly empty
  useEffect(() => {
    const keys = ['sort','order','dateFrom','dateTo','type','category','limit','offset'];
    const missing = keys.every(k => !searchParams.get(k));
    if (missing) {
      try {
        const raw = localStorage.getItem('tx_filters');
        if (raw) {
          const saved = JSON.parse(raw);
          const sp = new URLSearchParams(searchParams);
          keys.forEach(k => { if (saved[k] !== undefined && saved[k] !== null && saved[k] !== '') sp.set(k, String(saved[k])); });
          setSearchParams(sp, { replace: true });
        }
      } catch {}
    }
    // run once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading…</div></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Transactions</h1>

      {totals && (totals.income.length > 0 || totals.expense.length > 0) && (
        <div className="card p-4 mb-4" aria-label="Transactions totals">
          <div className="flex flex-wrap gap-6">
            <div>
              <div className="text-xs text-gray-600">Total Income</div>
              <div className="font-semibold">
                {totals.income.map(t => (
                  <span key={`inc-${t.currency}`} className="mr-4">{formatMoney(t.sum, t.currency)}</span>
                ))}
                {totals.income.length === 0 && <span>-</span>}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600">Total Expense</div>
              <div className="font-semibold">
                {totals.expense.map(t => (
                  <span key={`exp-${t.currency}`} className="mr-4">{formatMoney(t.sum, t.currency)}</span>
                ))}
                {totals.expense.length === 0 && <span>-</span>}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card p-4 mb-4" aria-label="Transactions filters">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Sort by</label>
            <div className="flex items-center gap-2">
              <select value={sort} onChange={handleSortChange} className="input input-bordered w-full">
                <option value="date">Date</option>
                <option value="amount">Amount</option>
                <option value="category">Category</option>
              </select>
              <button onClick={handleOrderToggle} className="btn btn-secondary" aria-label="Toggle sort order">
                {order === 'desc' ? 'Desc' : 'Asc'}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Date from</label>
            <input type="date" value={dateFrom} onChange={handleDateFrom} className="input input-bordered w-full" />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Date to</label>
            <input type="date" value={dateTo} onChange={handleDateTo} className="input input-bordered w-full" />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Type</label>
            <select value={type} onChange={handleType} className="input input-bordered w-full">
              <option value="">All</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Category</label>
            {categories.length > 0 ? (
              <select value={category} onChange={(e) => handleCategory({ target: { value: e.target.value } } as any)} className="input input-bordered w-full">
                <option value="">All</option>
                {categories.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            ) : (
              <input type="text" value={category} onChange={handleCategory} placeholder="e.g., transport" className="input input-bordered w-full" />
            )}
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Page size</label>
            <select value={pageLimit} onChange={handlePageSize} className="input input-bordered w-full">
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <div className="flex items-end"><button onClick={clearFilters} className="btn btn-outline w-full">Clear</button></div>
        </div>
      </div>

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
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(tx => (
                <tr key={tx.id} className="border-b last:border-0">
                  <td className="py-2">{new Date(tx.transaction_date).toLocaleDateString()}</td>
                  <td className="py-2">{tx.receipt_id ? <Link className="link" to={`/receipts/${tx.receipt_id}`}>{tx.merchant || '-'}</Link> : (tx.merchant || '-')}</td>
                  <td className="py-2">{tx.description}</td>
                  <td className="py-2">{tx.type}</td>
                  <td className="py-2 text-right">{formatMoney(tx.amount, tx.currency)}</td>
                  <td className="py-2">
                    <InlineCategoryEditor
                      value={tx.category || ''}
                      options={categories}
                      onChange={async (newVal) => {
                        // optimistic update
                        const prev = items;
                        setItems(items.map(it => it.id === tx.id ? { ...it, category: newVal || null } : it));
                        try {
                          const res = await apiClient.updateTransactionCategory(tx.id, newVal || null);
                          if (!res?.success) throw new Error(res?.message || 'Failed');
                          toast.success('Category updated');
                        } catch (e: any) {
                          // rollback on error
                          setItems(prev);
                          toast.error(e?.message || 'Failed to update category');
                        }
                      }}
                    />
                  </td>
                  <td className="py-2 text-right">
                    {tx.receipt_id ? <Link className="btn btn-xs" to={`/receipts/${tx.receipt_id}`}>Open receipt</Link> : <span className="text-gray-400">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-600">{`Showing ${pageInfo.totalCount ? (pageInfo.offset + 1) : 0}-${Math.min(pageInfo.offset + pageInfo.limit, pageInfo.totalCount)} of ${pageInfo.totalCount}`}</div>
          <div className="flex gap-2">
            <button className="btn btn-outline" onClick={() => setPage(Math.max(0, pageInfo.offset - pageInfo.limit))} disabled={!pageInfo.hasPrev}>Previous</button>
            <button className="btn btn-outline" onClick={() => setPage(pageInfo.offset + pageInfo.limit)} disabled={!pageInfo.hasNext}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionsPage;
 
// Inline category editor component
const InlineCategoryEditor: React.FC<{
  value: string;
  options: string[];
  onChange: (val: string) => void | Promise<void>;
}> = ({ value, options, onChange }) => {
  const [draft, setDraft] = useState<string>(value || '');
  const [saving, setSaving] = useState(false);

  useEffect(() => { setDraft(value || ''); }, [value]);

  const submit = async () => {
    if (saving) return;
    setSaving(true);
    try {
      await onChange(draft);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {options && options.length > 0 ? (
        <select
          className="input input-bordered"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={saving}
        >
          <option value="">-</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      ) : (
        <input
          className="input input-bordered"
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={saving}
          placeholder="e.g., transport"
        />
      )}
      <button className="btn btn-xs" onClick={submit} disabled={saving} aria-label="Save category">{saving ? 'Saving…' : 'Save'}</button>
    </div>
  );
};