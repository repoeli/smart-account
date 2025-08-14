import React from 'react';
import { useNavigate } from 'react-router-dom';

type Totals = { income: { currency: string; sum: string }[]; expense: { currency: string; sum: string }[] };

const formatMoney = (amount: string | number, currency: string) => {
  const value = typeof amount === 'number' ? amount : Number(amount);
  if (Number.isNaN(value)) return `${currency} ${amount}`;
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value); } catch { return `${currency} ${value.toFixed(2)}`; }
};

const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [range, setRange] = React.useState<'this_month' | 'last_month' | 'this_year' | 'custom'>('this_month');
  const [dateFrom, setDateFrom] = React.useState('');
  const [dateTo, setDateTo] = React.useState('');
  const [isFetching, setIsFetching] = React.useState(false);
  const [summaryError, setSummaryError] = React.useState<string | null>(null);
  const [totals, setTotals] = React.useState<Totals>({ income: [], expense: [] });
  const [byMonth, setByMonth] = React.useState<Array<{ month: string; currency: string; income: number; expense: number }>>([]);
  const [byCategory, setByCategory] = React.useState<Array<{ category: string; currency: string; income: number; expense: number }>>([]);
  const [byMerchant, setByMerchant] = React.useState<Array<{ merchant: string; currency: string; income: number; expense: number }>>([]);

  React.useEffect(() => {
    // hydrate saved
    try {
      const raw = localStorage.getItem('analytics_range');
      if (raw) {
        const s = JSON.parse(raw);
        if (s.range) setRange(s.range);
        if (s.dateFrom) setDateFrom(s.dateFrom);
        if (s.dateTo) setDateTo(s.dateTo);
      }
    } catch {}
  }, []);

  React.useEffect(() => {
    try { localStorage.setItem('analytics_range', JSON.stringify({ range, dateFrom, dateTo })); } catch {}
  }, [range, dateFrom, dateTo]);

  const load = React.useCallback(async () => {
    setIsFetching(true);
    try {
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const now = new Date();
      let df = dateFrom;
      let dt = dateTo;
      if (range !== 'custom') {
        let start: Date;
        let end: Date;
        if (range === 'last_month') {
          start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
          end = new Date(now.getFullYear(), now.getMonth(), 0);
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
      } else if (!df || !dt) {
        setIsFetching(false);
        return;
      }

      const url = new URL(`${apiBase}/transactions/summary/`);
      url.searchParams.set('dateFrom', df!);
      url.searchParams.set('dateTo', dt!);
      url.searchParams.set('groupBy', 'month,category,merchant');
      const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
      if (!res.ok) {
        setSummaryError('Failed to load analytics');
        setTotals({ income: [], expense: [] });
        setByMonth([]); setByCategory([]); setByMerchant([]);
        return;
      }
      const data = await res.json().catch(() => ({}));
      if (data?.success && data.totals) setTotals(data.totals);
      setByMonth(Array.isArray(data.byMonth) ? data.byMonth : []);
      setByCategory(Array.isArray(data.byCategory) ? data.byCategory : []);
      setByMerchant(Array.isArray(data.byMerchant) ? data.byMerchant : []);
      setSummaryError(null);
    } finally {
      setIsFetching(false);
    }
  }, [range, dateFrom, dateTo]);

  React.useEffect(() => { load(); }, [load]);

  const exportCsv = async () => {
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const url = new URL(`${apiBase}/reports/financial/overview.csv`);
    if (dateFrom) url.searchParams.set('dateFrom', dateFrom);
    if (dateTo) url.searchParams.set('dateTo', dateTo);
    const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
    if (!res.ok) return;
    const blob = await res.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'financial_overview.csv';
    document.body.appendChild(link); link.click(); link.remove();
  };

  const exportPdf = async () => {
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const url = new URL(`${apiBase}/reports/financial/overview.pdf`);
    if (dateFrom) url.searchParams.set('dateFrom', dateFrom);
    if (dateTo) url.searchParams.set('dateTo', dateTo);
    const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
    if (!res.ok) return;
    const blob = await res.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'financial_overview.pdf';
    document.body.appendChild(link); link.click(); link.remove();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="flex gap-2">
          <button className={`btn btn-outline ${range==='this_month'?'btn-active':''}`} onClick={() => setRange('this_month')}>This month</button>
          <button className={`btn btn-outline ${range==='last_month'?'btn-active':''}`} onClick={() => setRange('last_month')}>Last month</button>
          <button className={`btn btn-outline ${range==='this_year'?'btn-active':''}`} onClick={() => setRange('this_year')}>This year</button>
          <button className={`btn btn-outline ${range==='custom'?'btn-active':''}`} onClick={() => setRange('custom')}>Custom</button>
          <button className="btn btn-secondary" onClick={exportCsv}>Export CSV</button>
          <button className="btn btn-outline" onClick={exportPdf}>Export PDF</button>
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
          <button className="btn btn-primary" onClick={() => load()} disabled={isFetching}>Apply</button>
        </div>
      )}

      {summaryError && (
        <div className="mb-4 p-3 border border-yellow-200 bg-yellow-50 text-yellow-700 rounded flex items-center justify-between">
          <span>{summaryError}</span>
          <button className="btn-outline" onClick={() => load()} disabled={isFetching}>Retry</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-4">
          <div className="text-xs text-gray-600">Total Income</div>
          <div className="text-2xl font-semibold">{totals.income.length ? totals.income.map(t => <span key={`inc-${t.currency}`} className="mr-2">{formatMoney(t.sum, t.currency)}</span>) : formatMoney(0, 'GBP')}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-gray-600">Total Expenses</div>
          <div className="text-2xl font-semibold">{totals.expense.length ? totals.expense.map(t => <span key={`exp-${t.currency}`} className="mr-2">{formatMoney(t.sum, t.currency)}</span>) : formatMoney(0, 'GBP')}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-gray-600">Net</div>
          <div className="text-2xl font-semibold">
            {(() => {
              const curSet = new Set<string>([...totals.income.map(i => i.currency), ...totals.expense.map(e => e.currency)]);
              const parts: React.ReactNode[] = [];
              curSet.forEach(cur => {
                const inc = Number(totals.income.find(i => i.currency === cur)?.sum || 0);
                const exp = Number(totals.expense.find(e => e.currency === cur)?.sum || 0);
                parts.push(<span key={`net-${cur}`} className="mr-2">{formatMoney(inc - exp, cur)}</span>);
              });
              return parts.length ? parts : formatMoney(0, 'GBP');
            })()}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
		<div className="card p-4">
			<h3 className="font-semibold mb-3">Trend: Income vs Expense</h3>
			{(() => {
				const acc: Record<string, { income: number; expense: number }> = {};
				byMonth.forEach(r => {
					acc[r.month] = acc[r.month] || { income: 0, expense: 0 };
					acc[r.month].income += r.income;
					acc[r.month].expense += r.expense;
				});
				const rows = Object.entries(acc).sort((a,b)=>a[0].localeCompare(b[0]));
				if (rows.length === 0) return <div className="text-sm text-gray-500 italic">No data.</div>;
				const W = 640, H = 220, P = 30;
				const maxY = rows.reduce((m, [,v])=>Math.max(m, v.income, v.expense), 1);
				const denom = Math.max(1, rows.length - 1);
				const x = (i:number) => P + (i*(W-2*P))/denom;
				const y = (val:number) => H-P - (val/maxY)*(H-2*P);
				const incomePoints = rows.map(([_,v],i)=>`${x(i)},${y(v.income)}`).join(' ');
				const expensePoints = rows.map(([_,v],i)=>`${x(i)},${y(v.expense)}`).join(' ');
				return (
					<svg viewBox={`0 0 ${W} ${H}`} className="w-full h-56">
						<rect x={0} y={0} width={W} height={H} fill="#fff" />
						<line x1={P} y1={H-P} x2={W-P} y2={H-P} stroke="#ddd" />
						<line x1={P} y1={P} x2={P} y2={H-P} stroke="#ddd" />
						<polyline fill="none" stroke="#22c55e" strokeWidth={2} points={incomePoints} />
						<polyline fill="none" stroke="#f59e0b" strokeWidth={2} points={expensePoints} />
						{rows.map(([m],i)=> (<text key={m} x={x(i)} y={H-P+12} fontSize="10" textAnchor="middle" fill="#6b7280">{m.slice(2)}</text>))}
					</svg>
				);
			})()}
			<div className="mt-2 text-xs text-gray-500">Legend: <span className="inline-block w-3 h-3 bg-green-500 align-middle mr-1"></span>Income <span className="inline-block w-3 h-3 bg-yellow-500 align-middle mx-1"></span>Expense</div>
		</div>
		<div className="card p-4">
			<h3 className="font-semibold mb-3">Category Breakdown (Pie)</h3>
			{(() => {
				const acc: Record<string, number> = {};
				byCategory.forEach(r => { const key = r.category || 'uncategorized'; acc[key] = (acc[key] || 0) + r.income + r.expense; });
				const entries = Object.entries(acc).sort((a,b)=>b[1]-a[1]).slice(0,10);
				const total = entries.reduce((s,[,v])=>s+v, 0);
				if (total <= 0) return <div className="text-sm text-gray-500 italic">No data.</div>;
				const colors = ['#6366f1','#22c55e','#f59e0b','#ef4444','#06b6d4','#a855f7','#84cc16','#eab308','#fb7185','#93c5fd'];
				let start = 0; const CX = 110, CY = 110, R = 90;
				const polar = (cx:number,cy:number,r:number,a:number) => [cx + r*Math.cos((a-90)*Math.PI/180), cy + r*Math.sin((a-90)*Math.PI/180)];
				const arc = (s:number,e:number) => { const [sx,sy] = polar(CX,CY,R,s); const [ex,ey] = polar(CX,CY,R,e); const large = e - s > 180 ? 1 : 0; return `M ${CX} ${CY} L ${sx} ${sy} A ${R} ${R} 0 ${large} 1 ${ex} ${ey} Z`; };
				const slices = entries.map(([label,value],i) => { const angle = (value/total)*360; const path = arc(start, start+angle); const el = <path key={label} d={path} fill={colors[i%colors.length]} stroke="#fff" strokeWidth={1}/>; start += angle; return el; });
				return (
					<div className="flex items-start gap-6">
						<svg viewBox="0 0 220 220" className="w-56 h-56">{slices}</svg>
						<div className="text-xs space-y-1">
							{entries.map(([label,value],i)=> (
								<button
									key={label}
									onClick={() => navigate(`/transactions?${dateFrom?`dateFrom=${dateFrom}&`:''}${dateTo?`dateTo=${dateTo}&`:''}category=${encodeURIComponent(label)}`)}
									className="flex items-center gap-2 text-left hover:underline cursor-pointer"
									title={`View transactions in ${label}`}
								>
									<span className="inline-block w-3 h-3 rounded" style={{backgroundColor: colors[i%colors.length]}}></span>
									<span className="text-gray-700">{label}</span>
									<span className="text-gray-500">{formatMoney(value,'GBP')}</span>
								</button>
							))}
						</div>
					</div>
				);
			})()}
		</div>
        <div className="card p-4 lg:col-span-2">
          <h3 className="font-semibold mb-3">Top Merchants</h3>
          <div className="space-y-2">
            {(() => {
              const acc: Record<string, { total: number }> = {};
              byMerchant.forEach(r => {
                const key = r.merchant || 'unknown';
                acc[key] = acc[key] || { total: 0 };
                acc[key].total += r.income + r.expense;
              });
              const rows = Object.entries(acc).sort((a,b)=>b[1].total - a[1].total).slice(0,15);
              if (rows.length === 0) return <div className="text-sm text-gray-500 italic">No data.</div>;
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
    </div>
  );
};

export default AnalyticsPage;


