import { Outlet } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar, setMobileMenuOpen } from '../../store/slices/uiSlice';
import Sidebar from '../common/Sidebar';
import Header from '../common/Header';

const MainLayout = () => {
  const dispatch = useAppDispatch();
  const { sidebarOpen, mobileMenuOpen } = useAppSelector((state) => state.ui);

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  const handleCloseMobileMenu = () => {
    dispatch(setMobileMenuOpen(false));
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        mobileOpen={mobileMenuOpen}
        onClose={handleCloseMobileMenu}
      />

      {/* Main content */}
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${
        sidebarOpen ? 'lg:ml-64' : 'lg:ml-20'
      }`}>
        {/* Header */}
        <Header onToggleSidebar={handleToggleSidebar} />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="py-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile menu overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={handleCloseMobileMenu}
        />
      )}
    </div>
  );
};

export default MainLayout;