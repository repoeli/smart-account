import React, { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

const SubscriptionPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [plansLoading, setPlansLoading] = useState<boolean>(false);
  const [plans, setPlans] = useState<Array<{ id: string; nickname?: string; currency?: string; unit_amount?: number; interval?: string; product_id?: string; product_name?: string; product_metadata?: Record<string, any> | null; image?: string | null; payment_link_url?: string | null }>>([]);
  const [status, setStatus] = useState<{ tier?: string; status?: string; price_id?: string } | null>(null);
  const [current, setCurrent] = useState<{ status?: string; current_period_start?: number; current_period_end?: number; price_id?: string; plan?: { name?: string; currency?: string; unit_amount?: number; interval?: string } } | null>(null);
  const [usage, setUsage] = useState<{ receipts_this_month: number; max_receipts: number } | null>(null);
  const [invoices, setInvoices] = useState<Array<{ id?: string; created?: number; status?: string; currency?: string; amount_due?: number; hosted_invoice_url?: string; invoice_pdf?: string }>>([]);
  const [paymentMethods, setPaymentMethods] = useState<Array<{ id?: string; brand?: string; last4?: string; exp_month?: number; exp_year?: number; is_default?: boolean }>>([]);
  const [confirmPlan, setConfirmPlan] = useState<{ id: string; label: string } | null>(null);
  const [showCompare, setShowCompare] = useState<boolean>(false);

  const startCheckout = async (priceId?: string) => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await apiClient.startSubscriptionCheckout(priceId);
      if (res?.success && res?.url) {
        window.location.href = res.url;
        return;
      }
      toast.success('Subscription not configured yet');
    } catch (e: any) {
      toast.error(e?.message || 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  const openPortal = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await apiClient.openBillingPortal();
      if (res?.success && res?.url) {
        window.location.href = res.url;
        return;
      }
      toast.success('Billing portal not available yet');
    } catch (e: any) {
      toast.error(e?.message || 'Portal failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const run = async () => {
      setPlansLoading(true);
      try {
        const res = await apiClient.getSubscriptionPlans();
        if (res?.success) {
          let items = res.items || [];
          // Optional filtering to only keep three allowed plans when configured
          const envBasic = (import.meta as any).env?.VITE_STRIPE_PRICE_BASIC as string | undefined;
          const envPremium = (import.meta as any).env?.VITE_STRIPE_PRICE_PREMIUM as string | undefined;
          const envPlatinum = (import.meta as any).env?.VITE_STRIPE_PRICE_PLATINUM as string | undefined;
          const allowedIds = [envBasic, envPremium, envPlatinum].filter(Boolean) as string[];
          // Fallback to known IDs if env not provided
          const fallbackIds = ['price_1RkqyqCxGS83Likd7jXJ59u0','price_1Rkr2QCxGS83LikdomOLEVVC','price_1RkrAjCxGS83LikdMkacL3tt'];
          const idsToUse = allowedIds.length === 3 ? allowedIds : fallbackIds;
          const filtered = items.filter(p => idsToUse.includes(p.id));
          // If we matched at least one of desired ids, use filtered; otherwise show original
          items = filtered.length > 0 ? filtered : items;
          setPlans(items);
        }
        const st = await apiClient.getSubscriptionStatus();
        if (st?.success && st?.subscription) {
          setStatus({ tier: st.subscription.tier, status: st.subscription.status, price_id: (st.subscription as any).price_id });
        }
        const cur = await apiClient.getSubscriptionCurrent();
        if (cur?.success && cur?.subscription) setCurrent(cur.subscription as any);
        const us = await apiClient.getSubscriptionUsage();
        if (us?.success && us?.usage) setUsage(us.usage);
        try {
          const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
          const r = await fetch(`${apiBase}/subscriptions/invoices/?limit=10`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
          const d = await r.json().catch(()=>null);
          if (r.ok && d?.success && Array.isArray(d.items)) setInvoices(d.items);
        } catch {}
        try {
          const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
          const r = await fetch(`${apiBase}/subscriptions/payment-methods/`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
          const d = await r.json().catch(()=>null);
          if (r.ok && d?.success && Array.isArray(d.items)) setPaymentMethods(d.items);
        } catch {}
      } catch (e) {
        // ignore
      } finally {
        setPlansLoading(false);
      }
    };
    run();
  }, []);

  const sortedPlans = useMemo(() => {
    const order = ['Basic', 'Premium', 'Platinum'];
    return [...plans].sort((a, b) => {
      const ai = order.indexOf(a.nickname || '');
      const bi = order.indexOf(b.nickname || '');
      if (ai === -1 && bi === -1) return 0;
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }, [plans]);

  const isCurrentPlan = (p: { id: string; product_id?: string; nickname?: string; product_name?: string }) => {
    const currentPriceId = (status?.price_id || current?.price_id) as string | undefined;
    if (currentPriceId && currentPriceId === p.id) return true;
    const name = (p.nickname || p.product_name || '').toLowerCase();
    const tier = (status?.tier || '').toLowerCase();
    if (!currentPriceId && tier) {
      if (tier === 'basic' && name.includes('basic')) return true;
      if (tier === 'premium' && name.includes('premium')) return true;
      if (tier === 'enterprise' && (name.includes('platinum') || name.includes('enterprise'))) return true;
    }
    return false;
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Subscription</h1>
      <div className="card p-4">
        <p className="text-sm text-gray-600 mb-4">Manage your subscription. If Stripe is not configured, these actions will no-op.</p>
        {status && (
          <div className="mb-3 text-sm">
            <span className="font-medium">Current:</span> {status.tier || 'basic'} · {status.status || 'unknown'}
          </div>
        )}
        {current && (
          <div className="mb-3 text-xs text-gray-600">
            <div>Plan: {current.plan?.name || current.price_id || '—'} {current.plan?.unit_amount != null && current.plan?.currency ? `· ${(current.plan.unit_amount/100).toFixed(2)} ${current.plan.currency.toUpperCase()}/${current.plan.interval || ''}` : ''}</div>
            {(current.current_period_start && current.current_period_end) && (
              <div>Period: {new Date((current.current_period_start as number)*1000).toLocaleDateString()} → {new Date((current.current_period_end as number)*1000).toLocaleDateString()}</div>
            )}
          </div>
        )}
        {usage && (
          <div className="mb-3 text-xs text-gray-600">
            <div className="mb-1">Usage this month: {usage.receipts_this_month} / {usage.max_receipts < 0 ? '∞' : usage.max_receipts}</div>
            {usage.max_receipts > 0 && (
              <div className="h-2 bg-gray-100 rounded">
                <div className="h-2 bg-blue-500 rounded" style={{ width: `${Math.min(100, Math.round((usage.receipts_this_month / usage.max_receipts) * 100))}%` }} />
              </div>
            )}
          </div>
        )}
        <div className="flex gap-3 mb-4">
          <button className="btn btn-outline" onClick={openPortal} disabled={loading}>Open Billing Portal</button>
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Choose a plan</h2>
          <div className="mb-3">
            <button className="btn btn-outline btn-sm" onClick={() => setShowCompare(true)}>Compare plans</button>
          </div>
          {plansLoading && <div className="text-sm text-gray-500">Loading plans…</div>}
          {!plansLoading && sortedPlans.length === 0 && (
            <div className="text-sm text-gray-500">No plans found. You can still start a default checkout.</div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sortedPlans.map((p) => (
              <div key={p.id} className="border rounded p-3 flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  {p.image && <img src={p.image} alt={p.nickname || p.product_name || 'Plan'} className="w-10 h-10 rounded" />}
                  <div className="font-medium flex items-center gap-2">
                    {p.nickname || p.product_name || 'Plan'}
                    {String(p.product_metadata?.popular || '').replaceAll('"','') === 'true' && (
                      <span className="text-xxs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 border border-yellow-200">Popular</span>
                    )}
                    {isCurrentPlan(p) && (
                      <span className="text-xxs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">Current</span>
                    )}
                  </div>
                </div>
                {p.product_metadata?.features && (
                  <ul className="text-xs text-gray-600 list-disc ml-5">
                    {String(p.product_metadata.features).replaceAll('"','').split(',').slice(0,5).map((f: string, idx: number) => (
                      <li key={idx}>{f.trim()}</li>
                    ))}
                  </ul>
                )}
                <div className="text-sm text-gray-600">
                  {p.unit_amount != null ? `${(p.unit_amount / 100).toFixed(2)} ${p.currency?.toUpperCase() || ''}/${p.interval || ''}` : 'Price TBD'}
                </div>
                {p.product_metadata?.trial_days && (
                  <div className="text-xs text-gray-500">Trial: {String(p.product_metadata.trial_days).replaceAll('"','')} days</div>
                )}
                <div className="flex gap-2 mt-1 flex-wrap">
                  {!isCurrentPlan(p) && p.payment_link_url ? (
                    <a className="btn btn-outline" href={p.payment_link_url} target="_blank" rel="noreferrer">Open Payment Link</a>
                  ) : null}
                  <button className="btn btn-primary" disabled={loading || isCurrentPlan(p)} onClick={() => setConfirmPlan({ id: p.id, label: p.nickname || p.product_name || 'Plan' })}>
                    {loading ? 'Please wait…' : (current?.price_id === p.id || status?.price_id === p.id) ? 'Selected' : 'Choose plan'}
                  </button>
                </div>
              </div>
            ))}
          </div>
          {confirmPlan && (
            <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
              <div className="bg-white rounded shadow-md p-4 w-full max-w-sm">
                <div className="font-semibold mb-2">Confirm plan change</div>
                <div className="text-sm text-gray-700 mb-4">You are about to subscribe to <span className="font-medium">{confirmPlan.label}</span>. You will be redirected to Stripe to complete payment.</div>
                <div className="flex justify-end gap-2">
                  <button className="btn" onClick={() => setConfirmPlan(null)}>Cancel</button>
                  <button className="btn btn-primary" onClick={async()=>{ const pid=confirmPlan.id; setConfirmPlan(null); await startCheckout(pid); }}>Continue</button>
                </div>
              </div>
            </div>
          )}
          {showCompare && (
            <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
              <div className="bg-white rounded shadow-md p-4 w-full max-w-4xl">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold text-lg">Plan comparison</div>
                  <button className="btn btn-sm" onClick={()=>setShowCompare(false)}>Close</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left border-b">
                        <th className="py-2">Feature</th>
                        {sortedPlans.map(p => (
                          <th key={`h-${p.id}`} className="py-2">{p.nickname || p.product_name || 'Plan'}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(['receipt_limit','ocr_limit','storage_gb','user_limit','support_type','api_access'] as const).map(key => (
                        <tr key={key} className="border-b last:border-0">
                          <td className="py-2 capitalize">{key.replace('_',' ')}</td>
                          {sortedPlans.map(p => {
                            const meta = p.product_metadata || {} as any;
                            const raw = meta[key] ?? '';
                            const val = String(raw).replaceAll('"','');
                            return <td key={`${p.id}-${key}`} className="py-2">{val || '—'}</td>;
                          })}
                        </tr>
                      ))}
                      <tr className="border-b">
                        <td className="py-2">Price</td>
                        {sortedPlans.map(p => (
                          <td key={`${p.id}-price`} className="py-2">{p.unit_amount != null ? `${(p.unit_amount/100).toFixed(2)} ${p.currency?.toUpperCase()}/${p.interval}` : 'TBD'}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="py-2">Trial days</td>
                        {sortedPlans.map(p => (
                          <td key={`${p.id}-trial`} className="py-2">{String(p.product_metadata?.trial_days || '').replaceAll('"','') || '—'}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
          {sortedPlans.length === 0 && (
            <div className="mt-4">
              <button className="btn btn-primary" onClick={() => startCheckout()} disabled={loading}>{loading ? 'Please wait…' : 'Start Default Checkout'}</button>
            </div>
          )}
        </div>
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Recent Invoices</h2>
          {invoices.length === 0 && <div className="text-sm text-gray-500">No invoices found.</div>}
          {invoices.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Date</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Amount</th>
                  <th className="py-2">Links</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id} className="border-b last:border-0">
                    <td className="py-2">{inv.created ? new Date(inv.created*1000).toLocaleDateString() : '-'}</td>
                    <td className="py-2 capitalize">{inv.status || '-'}</td>
                    <td className="py-2">{inv.amount_due != null && inv.currency ? `${(inv.amount_due/100).toFixed(2)} ${inv.currency.toUpperCase()}` : '-'}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        {inv.hosted_invoice_url && <a className="link" href={inv.hosted_invoice_url} target="_blank" rel="noreferrer">View</a>}
                        {inv.invoice_pdf && <a className="link" href={inv.invoice_pdf} target="_blank" rel="noreferrer">PDF</a>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Payment Methods</h2>
          {paymentMethods.length === 0 && (
            <div className="text-sm text-gray-500">No saved payment methods. Use the Billing Portal to add or update cards.</div>
          )}
          {paymentMethods.length > 0 && (
            <div className="space-y-2">
              {paymentMethods.map(pm => (
                <div key={pm.id} className="flex items-center justify-between border rounded p-3">
                  <div className="text-sm text-gray-700">
                    <span className="font-medium capitalize">{pm.brand}</span> •••• {pm.last4} · exp {pm.exp_month}/{pm.exp_year}
                    {pm.is_default && <span className="ml-2 text-xxs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">Default</span>}
                  </div>
                  {!pm.is_default && (
                    <button className="btn btn-xs" onClick={async()=>{
                      try{
                        const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
                        const res = await fetch(`${apiBase}/subscriptions/payment-methods/`,{ method:'POST', headers:{ 'Content-Type':'application/json','Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` }, body: JSON.stringify({ payment_method_id: pm.id }) });
                        const data = await res.json();
                        if(res.ok && data?.success){
                          setPaymentMethods(paymentMethods.map(x => ({...x, is_default: x.id === pm.id})));
                        }
                      }catch{}
                    }}>Make default</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;


