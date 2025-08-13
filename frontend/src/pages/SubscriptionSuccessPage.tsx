import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/api';

const SubscriptionSuccessPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<any>(null);
  const [current, setCurrent] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const st = await apiClient.getSubscriptionStatus();
        const cur = await apiClient.getSubscriptionCurrent();
        if (st?.success) setStatus(st.subscription);
        if (cur?.success) setCurrent(cur.subscription);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="card p-6 text-center">
        <h1 className="text-2xl font-semibold mb-2">Subscription updated</h1>
        <p className="text-gray-600 mb-4">Your payment was processed by Stripe. Below is your current subscription status.</p>
        {loading ? (
          <div>Loading…</div>
        ) : (
          <div className="text-sm text-gray-700 space-y-2">
            <div>
              <span className="font-medium">Status:</span> {(status?.status || 'unknown').toString()} ({(status?.tier || 'basic').toString()})
            </div>
            {current?.plan && (
              <div>
                <span className="font-medium">Plan:</span> {(current.plan.name || current.price_id || '—').toString()}
              </div>
            )}
            {current?.current_period_start && current?.current_period_end && (
              <div>
                <span className="font-medium">Period:</span> {new Date(current.current_period_start * 1000).toLocaleDateString()} → {new Date(current.current_period_end * 1000).toLocaleDateString()}
              </div>
            )}
          </div>
        )}
        <div className="mt-4">
          <a className="btn btn-primary" href="/subscription">Go to Subscription</a>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionSuccessPage;


