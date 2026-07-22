"""
Customize JWT obtain to accept email/password and return user payload.
"""
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import UserSerializer


class WorkTaskMeTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        email = (attrs.get(self.username_field) or "").strip().lower()
        attrs[self.username_field] = email

        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if user and not user.email_verified:
            raise AuthenticationFailed(
                detail={
                    "detail": "Email not verified. Enter the OTP sent to your inbox.",
                    "requires_otp": True,
                    "email": email,
                }
            )
        if user and not user.is_active:
            raise AuthenticationFailed(
                detail={
                    "detail": "Account is inactive. Verify your email with the OTP code.",
                    "requires_otp": True,
                    "email": email,
                }
            )

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class WorkTaskMeTokenObtainPairView(TokenObtainPairView):
    serializer_class = WorkTaskMeTokenObtainPairSerializer
