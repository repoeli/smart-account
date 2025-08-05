"""
URL configuration for web interface.
"""

from django.urls import path
from django.http import HttpResponse

urlpatterns = [
    # Home page
    path('', lambda request: HttpResponse('Smart Accounts Management System - Web Interface'), name='home'),
    
    # Dashboard
    path('dashboard/', lambda request: HttpResponse('Dashboard'), name='dashboard'),
    
    # Health check
    path('health/', lambda request: HttpResponse('OK'), name='health_check'),
] 