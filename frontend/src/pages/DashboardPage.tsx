import { useAppSelector } from '../store';

const DashboardPage = () => {
  const { user } = useAppSelector((state) => state.auth);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">📄</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Receipts</h3>
              <p className="text-2xl font-semibold text-gray-900">0</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">💰</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Total Amount</h3>
              <p className="text-2xl font-semibold text-gray-900">£0.00</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">This Month</h3>
              <p className="text-2xl font-semibold text-gray-900">£0.00</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-medium">🏢</span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500">Business Expenses</h3>
              <p className="text-2xl font-semibold text-gray-900">£0.00</p>
            </div>
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