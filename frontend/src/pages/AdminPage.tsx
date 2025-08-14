import React, { useEffect, useState } from 'react';

const AdminPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

  const fetchJSON = async (url: string, options?: RequestInit) => {
    const res = await fetch(url, {
      ...(options || {}),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        ...(options?.headers || {}),
      },
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(data?.message || 'Request failed');
    return data;
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [s, d] = await Promise.all([
          fetchJSON(`${apiBase}/admin/settings/`),
          fetchJSON(`${apiBase}/admin/diagnostics/`),
        ]);
        setSettings(s?.settings || {});
        setDiagnostics(d?.diagnostics || {});
      } catch (e: any) {
        setError(e?.message || 'Failed to load admin data');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const save = async () => {
    try {
      setError(null);
      await fetchJSON(`${apiBase}/admin/settings/`, {
        method: 'PUT',
        body: JSON.stringify(settings || {}),
      });
      alert('Settings saved');
    } catch (e: any) {
      setError(e?.message || 'Failed to save');
    }
  };

  if (loading) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading…</div></div>;
  if (error) return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;

  // Helpers to ensure nested structure exists
  const ensure = (path: string[], fallback: any) => {
    setSettings((prev: any) => {
      const copy = { ...(prev || {}) };
      let cur = copy;
      for (let i = 0; i < path.length; i++) {
        const k = path[i];
        if (i === path.length - 1) {
          if (cur[k] === undefined) cur[k] = fallback;
        } else {
          cur[k] = cur[k] || {};
          cur = cur[k];
        }
      }
      return copy;
    });
  };

  const updateAt = (path: string[], value: any) => {
    setSettings((prev: any) => {
      const copy = { ...(prev || {}) };
      let cur = copy;
      for (let i = 0; i < path.length - 1; i++) {
        const k = path[i];
        cur[k] = cur[k] || {};
        cur = cur[k];
      }
      cur[path[path.length - 1]] = value;
      return copy;
    });
  };

  const s = settings || {};
  const plans = s.plans || {};
  const limits = plans.limits || { basic: 100, premium: 500, enterprise: -1 };
  const gates = plans.gates || { csv_export: { min_tier: 'premium' }, clients: { min_tier: 'premium' } };
  const ocr = s.ocr || { order: ['paddle_ocr', 'openai_vision'], fallback_enabled: true, review_threshold: 0.2 };
  const storage = s.storage || { cloudinary_folder: 'receipts', local_fallback: true, max_mb: 10 };
  const dashboard = s.dashboard || { summary_cache_ttl: 60, default_range: 'this_month' };
  const security = s.security || { cors_allowed_origins: ['http://localhost:5173'], audit_retention_days: 90 };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Admin Settings</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Settings sections */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-4">
            <h2 className="font-semibold mb-3">Subscription & Plans</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Basic monthly limit</label>
                <input type="number" className="input input-bordered w-full" value={limits.basic ?? 100}
                  onChange={(e)=>{ ensure(['plans','limits'], limits); updateAt(['plans','limits','basic'], Number(e.target.value)); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Premium monthly limit</label>
                <input type="number" className="input input-bordered w-full" value={limits.premium ?? 500}
                  onChange={(e)=>{ ensure(['plans','limits'], limits); updateAt(['plans','limits','premium'], Number(e.target.value)); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Enterprise monthly limit (-1 = ∞)</label>
                <input type="number" className="input input-bordered w-full" value={limits.enterprise ?? -1}
                  onChange={(e)=>{ ensure(['plans','limits'], limits); updateAt(['plans','limits','enterprise'], Number(e.target.value)); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">CSV Export min tier</label>
                <select className="input input-bordered w-full" value={gates.csv_export?.min_tier ?? 'premium'}
                  onChange={(e)=>{ ensure(['plans','gates','csv_export'], gates.csv_export || {min_tier:'premium'}); updateAt(['plans','gates','csv_export','min_tier'], e.target.value); }}>
                  <option value="basic">basic</option>
                  <option value="premium">premium</option>
                  <option value="enterprise">enterprise</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Clients feature min tier</label>
                <select className="input input-bordered w-full" value={gates.clients?.min_tier ?? 'premium'}
                  onChange={(e)=>{ ensure(['plans','gates','clients'], gates.clients || {min_tier:'premium'}); updateAt(['plans','gates','clients','min_tier'], e.target.value); }}>
                  <option value="basic">basic</option>
                  <option value="premium">premium</option>
                  <option value="enterprise">enterprise</option>
                </select>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">OCR & Processing</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Fallback enabled</label>
                <select className="input input-bordered w-full" value={ocr.fallback_enabled ? 'true' : 'false'}
                  onChange={(e)=>{ ensure(['ocr'], ocr); updateAt(['ocr','fallback_enabled'], e.target.value === 'true'); }}>
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Review threshold (0..1)</label>
                <input type="number" step="0.05" min={0} max={1} className="input input-bordered w-full" value={ocr.review_threshold ?? 0.2}
                  onChange={(e)=>{ ensure(['ocr'], ocr); updateAt(['ocr','review_threshold'], Number(e.target.value)); }} />
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Storage & Files</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Cloudinary folder</label>
                <input className="input input-bordered w-full" value={storage.cloudinary_folder ?? 'receipts'}
                  onChange={(e)=>{ ensure(['storage'], storage); updateAt(['storage','cloudinary_folder'], e.target.value); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Local fallback</label>
                <select className="input input-bordered w-full" value={storage.local_fallback ? 'true' : 'false'}
                  onChange={(e)=>{ ensure(['storage'], storage); updateAt(['storage','local_fallback'], e.target.value === 'true'); }}>
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Max upload size (MB)</label>
                <input type="number" className="input input-bordered w-full" value={storage.max_mb ?? 10}
                  onChange={(e)=>{ ensure(['storage'], storage); updateAt(['storage','max_mb'], Number(e.target.value)); }} />
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Dashboard & Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Summary cache TTL (sec)</label>
                <input type="number" className="input input-bordered w-full" value={dashboard.summary_cache_ttl ?? 60}
                  onChange={(e)=>{ ensure(['dashboard'], dashboard); updateAt(['dashboard','summary_cache_ttl'], Number(e.target.value)); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Default date range</label>
                <select className="input input-bordered w-full" value={dashboard.default_range ?? 'this_month'}
                  onChange={(e)=>{ ensure(['dashboard'], dashboard); updateAt(['dashboard','default_range'], e.target.value); }}>
                  <option value="this_month">this_month</option>
                  <option value="last_month">last_month</option>
                  <option value="this_year">this_year</option>
                </select>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Security</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div className="md:col-span-2">
                <label className="block text-xs text-gray-600 mb-1">CORS allowed origins (comma-separated)</label>
                <input className="input input-bordered w-full" value={(security.cors_allowed_origins || []).join(',')}
                  onChange={(e)=>{ ensure(['security'], security); updateAt(['security','cors_allowed_origins'], e.target.value.split(',').map(s=>s.trim()).filter(Boolean)); }} />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Audit retention days</label>
                <input type="number" className="input input-bordered w-full" value={security.audit_retention_days ?? 90}
                  onChange={(e)=>{ ensure(['security'], security); updateAt(['security','audit_retention_days'], Number(e.target.value)); }} />
              </div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">Raw JSON (advanced)</h2>
            <textarea
              className="w-full h-64 border rounded p-2 font-mono text-xs"
              value={JSON.stringify(settings || {}, null, 2)}
              onChange={(e) => {
                try { setSettings(JSON.parse(e.target.value)); } catch {}
              }}
            />
          </div>
        </div>

        {/* Right: Diagnostics & Analysis */}
        <div className="space-y-6">
          <div className="card p-4">
            <h2 className="font-semibold mb-2">Diagnostics</h2>
            <pre className="w-full h-64 border rounded p-2 font-mono text-xs overflow-auto">{JSON.stringify(diagnostics || {}, null, 2)}</pre>
            <div className="mt-2 flex gap-2">
              <a className="btn btn-outline" href={`${apiBase}/admin/analysis/export.csv`} target="_blank" rel="noreferrer">Export Analysis CSV</a>
              <button className="btn btn-outline" onClick={async () => {
                try {
                  const q = new URLSearchParams();
                  const df = prompt('dateFrom (YYYY-MM-DD)') || '';
                  const dt = prompt('dateTo (YYYY-MM-DD)') || '';
                  if (df) q.set('dateFrom', df);
                  if (dt) q.set('dateTo', dt);
                  const o = await fetchJSON(`${apiBase}/admin/analysis/overview/?${q.toString()}`);
                  alert(JSON.stringify(o?.metrics || {}, null, 2));
                } catch (e:any) { setError(e?.message || 'Failed to load analysis'); }
              }}>View Analysis</button>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex gap-2">
              <button className="btn btn-primary" onClick={save}>Save All</button>
              <button className="btn btn-outline" onClick={async () => {
                try { const s = await fetchJSON(`${apiBase}/admin/settings/`); setSettings(s?.settings || {}); } catch (e:any) { setError(e?.message || 'Reload failed'); }
              }}>Reload</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;


