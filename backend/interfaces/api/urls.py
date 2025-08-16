"""
URL configuration for API endpoints.
Defines routing for all REST API endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    HealthCheckView, FileInfoView, UserRegistrationView, UserLoginView, EmailVerificationView, UserProfileView,
    PasswordResetRequestView, PasswordResetConfirmView,
    ReceiptUploadView, ReceiptListView, ReceiptDetailView, ReceiptUpdateView, ReceiptManualCreateView,
    ReceiptReprocessView, ReceiptValidateView, ReceiptCategorizeView, ReceiptStatisticsView,
    ReceiptParseView, CategorySuggestView, CategoriesListView, TransactionsSummaryView, TransactionsExportCSVView, TransactionCreateView, ReceiptsCountView, ReceiptStorageMigrateView, OCRHealthView, ReceiptReplaceView, ReceiptReprocessHistoryView, AuditLogsView, SubscriptionCheckoutView, StripeWebhookView, SubscriptionPortalView, ClientsView, SubscriptionPlansView, ClientDetailView, SubscriptionStatusView, ClientsCountView, SubscriptionCurrentView, SubscriptionUsageView, SubscriptionInvoicesView, SubscriptionPaymentMethodsView, AdminSettingsView, AdminDiagnosticsView, AdminAnalysisOverviewView, AdminAnalysisExportCSVView, ReportsFinancialOverviewCSVView, ReportsFinancialOverviewPDFView,
    CategoryView, CategorySummaryView, IncomeExpenseSummaryView,
    StripeCheckoutView,
    FinancialReportCSVView,
)
from .management_views import (
    CreateFolderView, FolderDetailView, FolderListView, SearchReceiptsView,
    AddTagsToReceiptView, BulkOperationView, MoveReceiptsToFolderView, UserStatisticsView
)

app_name = 'api'

urlpatterns = [
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('files/info/', FileInfoView.as_view(), name='file-info'),
    
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/verify-email/', EmailVerificationView.as_view(), name='email-verify'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User management endpoints
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Receipt management endpoints
    path('receipts/upload/', ReceiptUploadView.as_view(), name='receipt-upload'),
    path('receipts/manual/', ReceiptManualCreateView.as_view(), name='receipt-manual-create'),
    path('receipts/parse/', ReceiptParseView.as_view(), name='receipt-parse'),
    path('receipts/count/', ReceiptsCountView.as_view(), name='receipt-count'),
    path('receipts/', ReceiptListView.as_view(), name='receipt-list'),
    # IMPORTANT: Place static 'search' route BEFORE dynamic '<receipt_id>' routes
    path('receipts/search/', SearchReceiptsView.as_view(), name='receipt-search'),
    path('receipts/<str:receipt_id>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipts/<str:receipt_id>/update/', ReceiptUpdateView.as_view(), name='receipt-update'),
    
    # US-005: Enhanced Receipt Processing endpoints
    path('receipts/<str:receipt_id>/reprocess/', ReceiptReprocessView.as_view(), name='receipt-reprocess'),
    path('receipts/<str:receipt_id>/validate/', ReceiptValidateView.as_view(), name='receipt-validate'),
    path('receipts/<str:receipt_id>/categorize/', ReceiptCategorizeView.as_view(), name='receipt-categorize'),
    path('receipts/<str:receipt_id>/storage/migrate/', ReceiptStorageMigrateView.as_view(), name='receipt-storage-migrate'),
    path('receipts/<str:receipt_id>/replace/', ReceiptReplaceView.as_view(), name='receipt-replace'),
    path('receipts/<str:receipt_id>/reprocess/history/', ReceiptReprocessHistoryView.as_view(), name='receipt-reprocess-history'),
    path('audit/logs/', AuditLogsView.as_view(), name='audit-logs'),
    path('ocr/health/', OCRHealthView.as_view(), name='ocr-health'),
    path('receipts/statistics/', ReceiptStatisticsView.as_view(), name='receipt-statistics'),
    # Sprint 2.2 endpoints (temporary stub implementations for UI wiring)
    path('categories/suggest/', CategorySuggestView.as_view(), name='category-suggest'),
    path('categories/', CategoriesListView.as_view(), name='categories-list'),
    path('transactions/summary/', TransactionsSummaryView.as_view(), name='transactions-summary'),
    path('transactions/export.csv', TransactionsExportCSVView.as_view(), name='transactions-export'),
    path('transactions/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<str:tx_id>/', TransactionCreateView.as_view(), name='transaction-update'),
    # Subscriptions (US-013/US-014 core wiring)
    path('subscriptions/checkout/', SubscriptionCheckoutView.as_view(), name='subscription-checkout'),
    path('subscriptions/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('subscriptions/portal/', SubscriptionPortalView.as_view(), name='subscription-portal'),
    path('subscriptions/plans/', SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('subscriptions/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscriptions/current/', SubscriptionCurrentView.as_view(), name='subscription-current'),
    path('subscriptions/usage/', SubscriptionUsageView.as_view(), name='subscription-usage'),
    path('subscriptions/invoices/', SubscriptionInvoicesView.as_view(), name='subscription-invoices'),
    path('subscriptions/payment-methods/', SubscriptionPaymentMethodsView.as_view(), name='subscription-payment-methods'),
    # Clients (US-015 minimal) – put count BEFORE detail to avoid matching as client_id
    path('clients/', ClientsView.as_view(), name='clients'),
    path('clients/count/', ClientsCountView.as_view(), name='clients-count'),
    path('clients/<str:client_id>/', ClientDetailView.as_view(), name='client-detail'),

    # Admin (settings & diagnostics)
    path('admin/settings/', AdminSettingsView.as_view(), name='admin-settings'),
    path('admin/diagnostics/', AdminDiagnosticsView.as_view(), name='admin-diagnostics'),
    path('admin/analysis/overview/', AdminAnalysisOverviewView.as_view(), name='admin-analysis-overview'),
    path('admin/analysis/export.csv', AdminAnalysisExportCSVView.as_view(), name='admin-analysis-export'),
    # Reports (user-scoped financial exports)
    path('reports/financial/overview.csv', ReportsFinancialOverviewCSVView.as_view(), name='reports-financial-overview-csv'),
    path('reports/financial/overview.pdf', ReportsFinancialOverviewPDFView.as_view(), name='reports-financial-overview-pdf'),
    path('reports/financial-csv/', FinancialReportCSVView.as_view(), name='financial-report-csv'),
    
    # US-006: Receipt Management and Organization endpoints
    path('folders/', FolderListView.as_view(), name='folder-list'),
    path('folders/create/', CreateFolderView.as_view(), name='folder-create'),
    path('folders/<str:folder_id>/', FolderDetailView.as_view(), name='folder-detail'),
    path('folders/<str:folder_id>/receipts/', MoveReceiptsToFolderView.as_view(), name='folder-receipts'),
    path('receipts/<str:receipt_id>/tags/', AddTagsToReceiptView.as_view(), name='receipt-tags'),
    path('receipts/bulk/', BulkOperationView.as_view(), name='receipt-bulk'),
    path('users/statistics/', UserStatisticsView.as_view(), name='user-statistics'),

    # Category Management (US-006)
    path('categories/', CategoryView.as_view(), name='category-list-create'),

    # Summary Endpoints (US-010)
    path('summary/categories/', CategorySummaryView.as_view(), name='summary-categories'),
    path('summary/income-expense/', IncomeExpenseSummaryView.as_view(), name='summary-income-expense'),

    # Subscription Management (US-013/US-014)
    path('subscriptions/checkout/', StripeCheckoutView.as_view(), name='subscriptions-checkout'),
] 