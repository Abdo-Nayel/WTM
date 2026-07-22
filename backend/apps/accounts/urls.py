from django.urls import path

from apps.accounts.views import (
    AuthProvidersView,
    CheckEmailView,
    MeOverviewView,
    MeView,
    RegisterFCMTokenView,
    RegisterView,
    ResendOTPView,
    SetPasswordView,
    SocialDevLoginView,
    SocialLoginView,
    VerifyOTPView,
)

urlpatterns = [
    path("check-email/", CheckEmailView.as_view(), name="auth-check-email"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="auth-resend-otp"),
    path("providers/", AuthProvidersView.as_view(), name="auth-providers"),
    path("social/", SocialLoginView.as_view(), name="auth-social"),
    path("social/dev/", SocialDevLoginView.as_view(), name="auth-social-dev"),
    path("set-password/", SetPasswordView.as_view(), name="auth-set-password"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/overview/", MeOverviewView.as_view(), name="auth-me-overview"),
    path("fcm-token/", RegisterFCMTokenView.as_view(), name="auth-fcm-token"),
]
