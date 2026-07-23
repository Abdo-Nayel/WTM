import hashlib
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Global user identity (Facebook-style).

    Tenancy is NOT on the user row — isolation lives on WorkspaceMembership
    and every TenantModel.workspace FK.
    """

    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"
        MICROSOFT = "microsoft", "Microsoft"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(
        max_length=16, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    # FCM device tokens for push notifications (simple JSON list)
    fcm_tokens = models.JSONField(default=list, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["email"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email


class EmailOTP(models.Model):
    """One-time code for email verification after register / resend."""

    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=64)
    purpose = models.CharField(max_length=16, choices=Purpose.choices, default=Purpose.REGISTER)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, email: str, purpose: str = Purpose.REGISTER, ttl_minutes: int = 10):
        email = email.strip().lower()
        cls.objects.filter(
            email=email, purpose=purpose, consumed_at__isnull=True
        ).update(consumed_at=timezone.now())
        code = f"{secrets.randbelow(1_000_000):06d}"
        row = cls.objects.create(
            email=email,
            code_hash=cls.hash_code(code),
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )
        return row, code

    def matches(self, code: str) -> bool:
        return secrets.compare_digest(self.code_hash, self.hash_code(str(code).strip()))

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None


def send_otp_email(email: str, code: str, purpose: str = "register") -> None:
    subject = "WorkTaskMe verification code"
    if purpose == EmailOTP.Purpose.LOGIN:
        subject = "WorkTaskMe login code"
    body = (
        f"Your WorkTaskMe verification code is: {code}\n\n"
        f"It expires in 10 minutes.\n\n"
        f"If you did not request this, you can ignore this email.\n\n"
        f"— WorkTaskMe\n"
    )
    # Always print to container logs so VPS operators can recover the code
    print(f"\n[WorkTaskMe OTP] email={email} code={code} purpose={purpose}\n", flush=True)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 — surface SMTP misconfig without 500
        print(f"[WorkTaskMe OTP] email send failed: {exc}", flush=True)
        # Keep registration/login flow usable; operator can read code from logs
        if settings.DEBUG:
            raise
        # In production: do not crash the request; email is best-effort
        return


class PasswordResetToken(models.Model):
    """One-time link token for forgot-password (web)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @staticmethod
    def hash_token(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, user, ttl_hours: int = 1):
        cls.objects.filter(user=user, consumed_at__isnull=True).update(
            consumed_at=timezone.now()
        )
        raw = secrets.token_urlsafe(32)
        row = cls.objects.create(
            user=user,
            token_hash=cls.hash_token(raw),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
        )
        return row, raw

    def matches(self, raw: str) -> bool:
        return secrets.compare_digest(self.token_hash, self.hash_token(str(raw).strip()))

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None


def send_password_reset_email(email: str, raw_token: str) -> None:
    """Send a styled HTML reset email (1-hour link)."""
    base = (getattr(settings, "FRONTEND_URL", "") or "http://127.0.0.1:8000").rstrip(
        "/"
    )
    # Canonical web path; SPA also accepts /?reset=TOKEN
    link = f"{base}/reset-password?token={raw_token}"
    subject = "Reset your WorkTaskMe password"
    text_body = (
        "We received a request to reset your WorkTaskMe password.\n\n"
        f"Open this link to choose a new password (expires in 1 hour):\n{link}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "— WorkTaskMe\n"
    )
    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" /></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0F172A;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F8FAFC;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#ffffff;border-radius:16px;border:1px solid #E2E8F0;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#4F46E5,#6366F1);padding:28px 28px 22px;color:#fff;">
            <div style="font-size:20px;font-weight:800;letter-spacing:-0.02em;">WorkTaskMe</div>
            <div style="opacity:.9;font-size:13px;margin-top:4px;">Password reset</div>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <h1 style="margin:0 0 12px;font-size:22px;line-height:1.3;">Reset your password</h1>
            <p style="margin:0 0 18px;color:#475569;font-size:15px;line-height:1.55;">
              We received a request to reset the password for <strong style="color:#0F172A;">{email}</strong>.
              This link expires in <strong>1 hour</strong>.
            </p>
            <p style="margin:0 0 24px;">
              <a href="{link}" style="display:inline-block;background:#4F46E5;color:#fff;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:10px;">
                Choose a new password
              </a>
            </p>
            <p style="margin:0 0 8px;color:#64748B;font-size:12px;line-height:1.5;word-break:break-all;">
              Or paste this URL into your browser:<br />{link}
            </p>
            <p style="margin:18px 0 0;color:#94A3B8;font-size:12px;line-height:1.5;">
              If you did not request a reset, you can safely ignore this email.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 22px;border-top:1px solid #E2E8F0;color:#94A3B8;font-size:12px;">
            © 2026 WorkTaskMe · Powered by LyomaStech
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    print(f"\n[WorkTaskMe RESET] email={email} link={link}\n", flush=True)
    try:
        send_mail(
            subject=subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_body,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[WorkTaskMe RESET] email send failed: {exc}", flush=True)
        if settings.DEBUG:
            raise
