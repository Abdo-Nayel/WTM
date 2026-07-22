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
