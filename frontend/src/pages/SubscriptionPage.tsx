import React, { useState } from 'react';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

const SubscriptionPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);

  const startCheckout = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await apiClient.startSubscriptionCheckout();
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

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Subscription</h1>
      <div className="card p-4">
        <p className="text-sm text-gray-600 mb-4">Manage your subscription. If Stripe is not configured, these actions will no-op.</p>
        <div className="flex gap-3">
          <button className="btn btn-primary" onClick={startCheckout} disabled={loading}>{loading ? 'Please wait…' : 'Start Subscription'}</button>
          <button className="btn btn-outline" onClick={openPortal} disabled={loading}>Open Billing Portal</button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;


