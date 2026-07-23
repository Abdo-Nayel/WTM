from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.captcha import CaptchaError, verify_captcha_token
from apps.accounts.models import EmailOTP, send_otp_email
from apps.accounts.social import (
    SocialAuthError,
    verify_google_id_token,
    verify_microsoft_id_token,
)
from apps.core.i18n import t

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    has_usable_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "phone",
            "email_verified",
            "auth_provider",
            "has_usable_password",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "email",
            "email_verified",
            "auth_provider",
            "has_usable_password",
            "date_joined",
        )

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()


class MeSerializer(UserSerializer):
    workspaces = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("workspaces",)

    def get_workspaces(self, obj):
        from apps.workspaces.models import WorkspaceMembership

        memberships = (
            WorkspaceMembership.objects.filter(
                user=obj, is_active=True, workspace__is_active=True
            )
            .select_related("workspace")
            .order_by("workspace__name")
        )
        return [
            {
                "id": str(m.workspace_id),
                "name": m.workspace.name,
                "slug": m.workspace.slug,
                "role": m.role,
            }
            for m in memberships
        ]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    not_a_bot = serializers.BooleanField()
    website = serializers.CharField(required=False, allow_blank=True, default="")
    captcha_token = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_email(self, value):
        return value.strip().lower()

    def validate_not_a_bot(self, value):
        if value is not True:
            raise serializers.ValidationError("Please confirm you are not a bot.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if (attrs.get("website") or "").strip():
            raise serializers.ValidationError({"detail": "Bot detected."})
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": t("passwords_mismatch", request=request)}
            )
        try:
            ip = request.META.get("REMOTE_ADDR") if request else None
            verify_captcha_token(attrs.get("captcha_token"), remote_ip=ip)
        except CaptchaError as exc:
            raise serializers.ValidationError({"captcha_token": str(exc)}) from exc

        email = attrs["email"]
        existing = User.objects.filter(email=email).first()
        if existing and existing.email_verified and existing.is_active:
            raise serializers.ValidationError(
                {"email": "An account with this email already exists. Please sign in."}
            )
        attrs["_existing"] = existing
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        validated_data.pop("not_a_bot")
        validated_data.pop("website", None)
        validated_data.pop("captcha_token", None)
        existing = validated_data.pop("_existing", None)
        password = validated_data.pop("password")
        email = validated_data["email"]

        if existing:
            user = existing
            user.set_password(password)
            user.first_name = validated_data.get("first_name") or user.first_name
            user.last_name = validated_data.get("last_name") or user.last_name
            user.is_active = False
            user.email_verified = False
            user.auth_provider = User.AuthProvider.EMAIL
            user.save()
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=validated_data.get("first_name") or "",
                last_name=validated_data.get("last_name") or "",
                is_active=False,
                email_verified=False,
                auth_provider=User.AuthProvider.EMAIL,
            )

        otp_row, code = EmailOTP.issue(
            email, purpose=EmailOTP.Purpose.REGISTER, ttl_minutes=10
        )
        send_otp_email(email, code, purpose=EmailOTP.Purpose.REGISTER)
        user._otp_code_debug = code  # noqa: SLF001
        user._otp_id = otp_row.id
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)
    purpose = serializers.ChoiceField(
        choices=EmailOTP.Purpose.choices, default=EmailOTP.Purpose.REGISTER
    )

    def validate_email(self, value):
        return value.strip().lower()

    def save(self, **kwargs):
        email = self.validated_data["email"]
        code = self.validated_data["code"]
        purpose = self.validated_data["purpose"]
        otp = (
            EmailOTP.objects.filter(
                email=email, purpose=purpose, consumed_at__isnull=True
            )
            .order_by("-created_at")
            .first()
        )
        if not otp:
            raise serializers.ValidationError({"code": "No active code. Request a new one."})
        if otp.is_expired:
            raise serializers.ValidationError({"code": "Code expired. Request a new one."})
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        if otp.attempts > 8:
            otp.consumed_at = otp.consumed_at or otp.created_at
            otp.save(update_fields=["consumed_at"])
            raise serializers.ValidationError({"code": "Too many attempts. Request a new code."})
        if not otp.matches(code):
            raise serializers.ValidationError({"code": "Invalid verification code."})

        from django.utils import timezone

        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Account not found. Register first."})
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(
        choices=EmailOTP.Purpose.choices, default=EmailOTP.Purpose.REGISTER
    )
    captcha_token = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        request = self.context.get("request")
        try:
            ip = request.META.get("REMOTE_ADDR") if request else None
            verify_captcha_token(attrs.get("captcha_token"), remote_ip=ip)
        except CaptchaError as exc:
            raise serializers.ValidationError({"captcha_token": str(exc)}) from exc
        return attrs

    def save(self, **kwargs):
        email = self.validated_data["email"]
        purpose = self.validated_data["purpose"]
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": "Account not found."})
        if purpose == EmailOTP.Purpose.REGISTER and user.email_verified:
            raise serializers.ValidationError({"email": "Email is already verified. Sign in."})
        if purpose == EmailOTP.Purpose.RESET and not user.is_active:
            raise serializers.ValidationError({"email": "Account is disabled."})
        otp_row, code = EmailOTP.issue(email, purpose=purpose, ttl_minutes=10)
        send_otp_email(email, code, purpose=purpose)
        return {"email": email, "code": code, "otp_id": otp_row.id}


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["google", "microsoft"])
    credential = serializers.CharField()

    def save(self, **kwargs):
        provider = self.validated_data["provider"]
        credential = self.validated_data["credential"]
        try:
            if provider == "google":
                profile = verify_google_id_token(credential)
            else:
                profile = verify_microsoft_id_token(credential)
        except SocialAuthError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        email = profile["email"]
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=None,
                first_name=profile.get("first_name") or "",
                last_name=profile.get("last_name") or "",
                is_active=True,
                email_verified=True,
                auth_provider=provider,
            )
        else:
            user.email_verified = True
            user.is_active = True
            if not user.first_name and profile.get("first_name"):
                user.first_name = profile["first_name"]
            if not user.last_name and profile.get("last_name"):
                user.last_name = profile["last_name"]
            if user.auth_provider == User.AuthProvider.EMAIL:
                user.auth_provider = provider
            user.save()

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)
    current_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, default=""
    )

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        user = self.context["request"].user
        if user.has_usable_password():
            current = attrs.get("current_password") or ""
            if not current or not user.check_password(current):
                raise serializers.ValidationError(
                    {"current_password": "Current password is incorrect."}
                )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class FCMTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)

    def save(self, **kwargs):
        user = self.context["request"].user
        token = self.validated_data["token"]
        tokens = list(user.fcm_tokens or [])
        if token not in tokens:
            tokens.append(token)
            user.fcm_tokens = tokens
            user.save(update_fields=["fcm_tokens"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Send a 6-digit OTP for forgot-password. Requires a registered active email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        email = attrs["email"]
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError(
                {"email": "No account found for this email. Create an account first."}
            )
        if not user.is_active:
            raise serializers.ValidationError({"email": "This account is disabled."})
        attrs["_user"] = user
        return attrs

    def save(self, **kwargs):
        email = self.validated_data["email"]
        otp_row, code = EmailOTP.issue(
            email, purpose=EmailOTP.Purpose.RESET, ttl_minutes=10
        )
        try:
            send_otp_email(email, code, purpose=EmailOTP.Purpose.RESET)
        except Exception:
            pass
        result = {"email": email, "exists": True, "next": "otp"}
        if settings.DEBUG:
            result["otp_debug"] = code
            result["otp_id"] = otp_row.id
        return result


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Verify reset OTP, set a new password, and return JWT (auto sign-in)."""

    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        email = attrs["email"]
        code = attrs["code"]
        otp = (
            EmailOTP.objects.filter(
                email=email,
                purpose=EmailOTP.Purpose.RESET,
                consumed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if not otp:
            raise serializers.ValidationError(
                {"code": "No active code. Request a new one."}
            )
        if otp.is_expired:
            raise serializers.ValidationError(
                {"code": "Code expired. Request a new one."}
            )
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        if otp.attempts > 8:
            otp.consumed_at = otp.consumed_at or otp.created_at
            otp.save(update_fields=["consumed_at"])
            raise serializers.ValidationError(
                {"code": "Too many attempts. Request a new code."}
            )
        if not otp.matches(code):
            raise serializers.ValidationError({"code": "Invalid verification code."})
        user = User.objects.filter(email=email).first()
        if not user or not user.is_active:
            raise serializers.ValidationError({"email": "Account not found."})
        attrs["_otp_row"] = otp
        attrs["_user"] = user
        return attrs

    def save(self, **kwargs):
        from django.utils import timezone

        otp = self.validated_data["_otp_row"]
        user = self.validated_data["_user"]
        user.set_password(self.validated_data["new_password"])
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["password", "email_verified", "is_active"])
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
            "detail": "Password updated.",
        }
