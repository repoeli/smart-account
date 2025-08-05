"""
URL configuration for API interface.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView,
    UserLoginView,
    CustomTokenObtainPairView,
    EmailVerificationView,
    UserProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ReceiptUploadView,
    ReceiptListView,
    ReceiptDetailView,
    ReceiptUpdateView,
    health_check
)

# Create router for API endpoints
router = DefaultRouter()

# Register viewsets when they are created
# router.register(r'receipts', ReceiptViewSet, basename='receipt')
# router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    # API v1 endpoints
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User profile endpoints
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Receipt endpoints
    path('receipts/upload/', ReceiptUploadView.as_view(), name='receipt-upload'),
    path('receipts/', ReceiptListView.as_view(), name='receipt-list'),
    path('receipts/<uuid:receipt_id>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipts/<uuid:receipt_id>/update/', ReceiptUpdateView.as_view(), name='receipt-update'),
    
    # Health check endpoint
    path('health/', health_check, name='health_check'),
] 