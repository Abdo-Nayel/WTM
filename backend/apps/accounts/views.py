from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.captcha import captcha_config
from apps.accounts.serializers import (
    FCMTokenSerializer,
    MeSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    SetPasswordSerializer,
    SocialLoginSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()


class CheckEmailView(APIView):
    """
    Atlassian-style step 1: look up email and decide next auth step.
    POST { "email": "..." }
    -> exists+verified -> password
    -> exists+unverified -> send OTP -> otp
    -> missing -> register
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return Response({"detail": "Enter a valid email."}, status=400)

        user = User.objects.filter(email=email).first()
        if user is None:
            return Response(
                {
                    "email": email,
                    "exists": False,
                    "verified": False,
                    "next": "register",
                }
            )

        if user.email_verified and user.is_active:
            return Response(
                {
                    "email": email,
                    "exists": True,
                    "verified": True,
                    "has_usable_password": user.has_usable_password(),
                    "next": "password",
                    "auth_provider": user.auth_provider,
                }
            )

        # Unverified — (re)send OTP so they can finish signup
        from apps.accounts.models import EmailOTP, send_otp_email

        otp_row, code = EmailOTP.issue(
            email, purpose=EmailOTP.Purpose.REGISTER, ttl_minutes=10
        )
        try:
            send_otp_email(email, code, purpose=EmailOTP.Purpose.REGISTER)
        except Exception:
            pass
        payload = {
            "email": email,
            "exists": True,
            "verified": False,
            "next": "otp",
            "otp_expires_minutes": 10,
        }
        if settings.DEBUG:
            payload["otp_debug"] = code
        return Response(payload)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        payload = {
            "detail": "Account created. Enter the OTP sent to your email to verify.",
            "email": user.email,
            "requires_otp": True,
            "otp_expires_minutes": 10,
        }
        if settings.DEBUG:
            payload["otp_debug"] = getattr(user, "_otp_code_debug", None)
        return Response(payload, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = ResendOTPSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        result = ser.save()
        payload = {
            "detail": "A new verification code was sent to your email.",
            "email": result["email"],
            "otp_expires_minutes": 10,
        }
        if settings.DEBUG:
            payload["otp_debug"] = result.get("code")
        return Response(payload, status=status.HTTP_200_OK)


class AuthProvidersView(APIView):
    """Which social / captcha providers are configured (for SPA buttons)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        google_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "") or ""
        ms_id = getattr(settings, "MICROSOFT_OAUTH_CLIENT_ID", "") or ""
        debug = bool(settings.DEBUG)
        cap = captcha_config()
        return Response(
            {
                "email": True,
                "google": bool(google_id) or debug,
                "google_client_id": google_id,
                "microsoft": bool(ms_id) or debug,
                "microsoft_client_id": ms_id,
                "microsoft_tenant": getattr(settings, "MICROSOFT_OAUTH_TENANT", "common"),
                "debug_social": debug,
                "captcha": cap,
                "otp_expires_minutes": 10,
            }
        )


class SocialLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = SocialLoginSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        data = ser.save()
        return Response(data, status=status.HTTP_200_OK)


class SocialDevLoginView(APIView):
    """Local-only mock Google/Microsoft when OAuth client IDs are not set (DEBUG)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.DEBUG:
            return Response(
                {"detail": "Dev social login is only available when DEBUG=True."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from rest_framework_simplejwt.tokens import RefreshToken

        provider = (request.data.get("provider") or "").strip().lower()
        if provider not in ("google", "microsoft"):
            return Response({"detail": "provider must be google or microsoft"}, status=400)
        email = (request.data.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return Response({"detail": "A valid email is required."}, status=400)
        first_name = (request.data.get("first_name") or "").strip()[:150]
        last_name = (request.data.get("last_name") or "").strip()[:150]

        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=None,
                first_name=first_name or provider.title(),
                last_name=last_name or "User",
                is_active=True,
                email_verified=True,
                auth_provider=provider,
            )
        else:
            user.email_verified = True
            user.is_active = True
            user.auth_provider = provider
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "dev_mock": True,
            }
        )


class SetPasswordView(APIView):
    """Set or change local password (useful after Google/Microsoft SSO)."""

    def post(self, request):
        ser = SetPasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(
            {
                "detail": "Password updated. You can now sign in with email and password.",
                "user": UserSerializer(request.user).data,
            }
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserSerializer
        return MeSerializer


class MeOverviewView(APIView):
    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)


class RegisterFCMTokenView(APIView):
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "FCM token registered."}, status=status.HTTP_200_OK)


LoginView = TokenObtainPairView
