import React, { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

const SubscriptionPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [plansLoading, setPlansLoading] = useState<boolean>(false);
  const [plans, setPlans] = useState<Array<{ id: string; nickname?: string; currency?: string; unit_amount?: number; interval?: string }>>([]);
  const [status, setStatus] = useState<{ tier?: string; status?: string } | null>(null);

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
          setPlans(res.items || []);
        }
        const st = await apiClient.getSubscriptionStatus();
        if (st?.success && st?.subscription) {
          setStatus({ tier: st.subscription.tier, status: st.subscription.status });
        }
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
        <div className="flex gap-3 mb-4">
          <button className="btn btn-outline" onClick={openPortal} disabled={loading}>Open Billing Portal</button>
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-2">Choose a plan</h2>
          {plansLoading && <div className="text-sm text-gray-500">Loading plans…</div>}
          {!plansLoading && sortedPlans.length === 0 && (
            <div className="text-sm text-gray-500">No plans found. You can still start a default checkout.</div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sortedPlans.map((p) => (
              <div key={p.id} className="border rounded p-3 flex flex-col gap-2">
                <div className="font-medium">{p.nickname || 'Plan'}</div>
                <div className="text-sm text-gray-600">
                  {p.unit_amount != null ? `${(p.unit_amount / 100).toFixed(2)} ${p.currency?.toUpperCase() || ''}/${p.interval || ''}` : 'Price TBD'}
                </div>
                <button className="btn btn-primary mt-1" disabled={loading} onClick={() => startCheckout(p.id)}>
                  {loading ? 'Please wait…' : 'Subscribe'}
                </button>
              </div>
            ))}
          </div>
          {sortedPlans.length === 0 && (
            <div className="mt-4">
              <button className="btn btn-primary" onClick={() => startCheckout()} disabled={loading}>{loading ? 'Please wait…' : 'Start Default Checkout'}</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;


