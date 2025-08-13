import React from 'react';

const SubscriptionCancelPage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="card p-6 text-center">
        <h1 className="text-2xl font-semibold mb-2">Subscription not completed</h1>
        <p className="text-gray-600 mb-4">You canceled or closed the Stripe Checkout session. You can try again at any time.</p>
        <div className="mt-4">
          <a className="btn btn-primary" href="/subscription">Back to Subscription</a>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionCancelPage;


