import { useAppSelector } from '../store';

const ProfilePage = () => {
  const { user } = useAppSelector((state) => state.auth);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>
      
      <div className="space-y-6">
        {/* User Info Card */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="form-label">First Name</label>
                <input 
                  type="text" 
                  className="input-field" 
                  defaultValue={user?.first_name}
                  readOnly
                />
              </div>
              <div>
                <label className="form-label">Last Name</label>
                <input 
                  type="text" 
                  className="input-field" 
                  defaultValue={user?.last_name}
                  readOnly
                />
              </div>
            </div>
            <div>
              <label className="form-label">Email Address</label>
              <input 
                type="email" 
                className="input-field" 
                defaultValue={user?.email}
                readOnly
              />
            </div>
            <div>
              <label className="form-label">Account Type</label>
              <input 
                type="text" 
                className="input-field" 
                defaultValue={user?.user_type}
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Account Status */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Account Status</h3>
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              user?.status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {user?.status}
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              user?.is_verified 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {user?.is_verified ? 'Verified' : 'Unverified'}
            </div>
            <div className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 capitalize">
              {user?.subscription_tier} Plan
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-4">
          <button className="btn-primary">
            Edit Profile
          </button>
          <button className="btn-secondary">
            Change Password
          </button>
          <button className="btn-danger">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;