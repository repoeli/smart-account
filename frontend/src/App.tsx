import { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './store';
import { getCurrentUser } from './store/slices/authSlice';
import ProtectedRoute from './components/ProtectedRoute';
import { navigation } from './services/navigation';

// Import pages (we'll create these next)
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import EmailVerificationPage from './pages/auth/EmailVerificationPage';
import AccountingCompanyRegisterPage from './pages/auth/AccountingCompanyRegisterPage';
import DashboardPage from './pages/DashboardPage';
import ReceiptsPage from './pages/ReceiptsPage';
import ReceiptDetailPage from './pages/ReceiptDetailPage';
import ReceiptUploadPage from './pages/receipts/ReceiptUploadPage';
import ReceiptManualCreatePage from './pages/receipts/ReceiptManualCreatePage';
import OCRResultsPage from './pages/receipts/OCRResultsPage';
import ProfilePage from './pages/ProfilePage';
import TransactionsPage from './pages/TransactionsPage';
import AuditPage from './pages/AuditPage';
import ClientsPage from './pages/ClientsPage';
import SubscriptionPage from './pages/SubscriptionPage';
import SubscriptionSuccessPage from './pages/SubscriptionSuccessPage';
import SubscriptionCancelPage from './pages/SubscriptionCancelPage';
import AdminPage from './pages/AdminPage';
import AnalyticsPage from './pages/AnalyticsPage';
import FoldersPage from './pages/FoldersPage';
import MultiClientDashboardPage from './pages/MultiClientDashboardPage';
import ClientDetailPage from './pages/ClientDetailPage';
import ReportsPage from './pages/ReportsPage';

// Layouts
import AuthLayout from './components/layouts/AuthLayout';
import MainLayout from './components/layouts/MainLayout';

const NavigationHandler = () => {
  const navigate = useNavigate();
  useEffect(() => {
    navigation.navigate = navigate;
  }, [navigate]);
  return null;
};

function App() {
  const dispatch = useAppDispatch();
  const { token } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Always try to hydrate user if we have a token
    if (token) {
      dispatch(getCurrentUser());
    }
  }, [dispatch, token]);

  return (
    <div className="App">
      <NavigationHandler />
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Auth routes */}
        <Route path="/auth" element={
          <ProtectedRoute requireAuth={false}>
            <AuthLayout />
          </ProtectedRoute>
        }>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="register/accounting-company" element={<AccountingCompanyRegisterPage />} />
          <Route path="verify-email" element={<EmailVerificationPage />} />
        </Route>

        {/* Protected routes */}
        <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="multi-client-dashboard" element={<MultiClientDashboardPage />} />
          <Route path="receipts" element={<ReceiptsPage />} />
          <Route path="folders" element={<FoldersPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="receipts/upload" element={<ReceiptUploadPage />} />
          <Route path="receipts/new" element={<ReceiptManualCreatePage />} />
          <Route path="receipts/:id/ocr" element={<OCRResultsPage />} />
          <Route path="receipts/:id" element={<ReceiptDetailPage />} />
          <Route path="clients" element={<ClientsPage />} />
          <Route path="clients/:id" element={<ClientDetailPage />} />
          <Route path="subscription" element={<SubscriptionPage />} />
          <Route path="subscription/success" element={<SubscriptionSuccessPage />} />
          <Route path="subscription/cancel" element={<SubscriptionCancelPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </div>
  );
}

export default App;
