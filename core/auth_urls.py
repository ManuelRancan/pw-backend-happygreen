# core/auth_urls.py
from django.urls import path
from .auth_views import LoginView, RegisterView, ResendVerificationView, VerifyEmailView, VerifyOTPView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('verify-otp/<int:userId>/', VerifyOTPView.as_view(), name='verify-otp'),  # Aggiungi questa riga
]