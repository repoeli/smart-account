"""
URL configuration for API endpoints.
Defines routing for all REST API endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    HealthCheckView, UserRegistrationView, UserLoginView, EmailVerificationView, UserProfileView,
    PasswordResetRequestView, PasswordResetConfirmView,
    ReceiptUploadView, ReceiptListView, ReceiptDetailView, ReceiptUpdateView,
    ReceiptReprocessView, ReceiptValidateView, ReceiptCategorizeView, ReceiptStatisticsView
)
from .management_views import (
    CreateFolderView, FolderDetailView, FolderListView, SearchReceiptsView,
    AddTagsToReceiptView, BulkOperationView, MoveReceiptsToFolderView, UserStatisticsView
)

app_name = 'api'

urlpatterns = [
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
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
    path('receipts/', ReceiptListView.as_view(), name='receipt-list'),
    path('receipts/<str:receipt_id>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipts/<str:receipt_id>/update/', ReceiptUpdateView.as_view(), name='receipt-update'),
    
    # US-005: Enhanced Receipt Processing endpoints
    path('receipts/<str:receipt_id>/reprocess/', ReceiptReprocessView.as_view(), name='receipt-reprocess'),
    path('receipts/<str:receipt_id>/validate/', ReceiptValidateView.as_view(), name='receipt-validate'),
    path('receipts/<str:receipt_id>/categorize/', ReceiptCategorizeView.as_view(), name='receipt-categorize'),
    path('receipts/statistics/', ReceiptStatisticsView.as_view(), name='receipt-statistics'),
    
    # US-006: Receipt Management and Organization endpoints
    path('folders/', FolderListView.as_view(), name='folder-list'),
    path('folders/create/', CreateFolderView.as_view(), name='folder-create'),
    path('folders/<str:folder_id>/', FolderDetailView.as_view(), name='folder-detail'),
    path('folders/<str:folder_id>/receipts/', MoveReceiptsToFolderView.as_view(), name='folder-receipts'),
    path('receipts/search/', SearchReceiptsView.as_view(), name='receipt-search'),
    path('receipts/<str:receipt_id>/tags/', AddTagsToReceiptView.as_view(), name='receipt-tags'),
    path('receipts/bulk/', BulkOperationView.as_view(), name='receipt-bulk'),
    path('users/statistics/', UserStatisticsView.as_view(), name='user-statistics'),
] 