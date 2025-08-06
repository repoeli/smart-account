import { Outlet } from 'react-router-dom';
import { APP_CONFIG } from '../../constants/config';

const AuthLayout = () => {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding/Image */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 to-primary-700 relative">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative z-10 flex flex-col justify-center items-center p-12 text-white">
          <div className="max-w-md text-center">
            <h1 className="text-4xl font-bold mb-6">{APP_CONFIG.NAME}</h1>
            <p className="text-xl mb-8 text-blue-100">
              Streamline your receipt management with intelligent OCR and smart organization
            </p>
            <div className="grid grid-cols-1 gap-4 text-left">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-200 rounded-full"></div>
                <span>Automatic receipt scanning with OCR</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-200 rounded-full"></div>
                <span>Smart categorization and organization</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-200 rounded-full"></div>
                <span>Business expense tracking</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-200 rounded-full"></div>
                <span>HMRC-compatible exports</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Auth Form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div className="text-center lg:hidden mb-8">
            <h1 className="text-2xl font-bold text-gray-900">{APP_CONFIG.NAME}</h1>
            <p className="text-gray-600 mt-2">Smart Receipt Management</p>
          </div>
          
          <Outlet />
          
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>&copy; 2024 {APP_CONFIG.NAME}. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;