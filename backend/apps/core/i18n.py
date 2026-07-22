"""
Lightweight AR/EN translation helper for API error strings.

Prefer `?lang=ar|en` or the Accept-Language header (via LocaleMiddleware).
"""
from __future__ import annotations

from typing import Any

SUPPORTED = ("en", "ar")
DEFAULT_LANG = "en"

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "workspace_required": "X-Workspace-Id header is required for this endpoint.",
        "workspace_not_found": "Workspace not found.",
        "workspace_forbidden": "You are not a member of this workspace.",
        "admin_required": "Admin required.",
        "admin_required_invite": "Admin required to invite.",
        "membership_not_found": "Membership not found.",
        "invalid_role": "Invalid role.",
        "invite_not_found": "Not found.",
        "invalid_invite_token": "Invalid invitation token.",
        "invite_already_accepted": "Invitation already accepted.",
        "invite_expired": "Invitation has expired.",
        "invite_email_mismatch": "Logged-in user email does not match the invitation.",
        "only_admins_invite_admins": "Only workspace admins can invite other admins.",
        "project_id_required": "This field is required.",
        "project_not_found": "Project not found in workspace.",
        "subtask_needs_parent": "Sub-tasks require a parent task.",
        "passwords_mismatch": "Passwords do not match.",
    },
    "ar": {
        "workspace_required": "رأس X-Workspace-Id مطلوب لهذا المسار.",
        "workspace_not_found": "مساحة العمل غير موجودة.",
        "workspace_forbidden": "لست عضواً في مساحة العمل هذه.",
        "admin_required": "مطلوب صلاحية مسؤول.",
        "admin_required_invite": "مطلوب صلاحية مسؤول لدعوة الأعضاء.",
        "membership_not_found": "العضوية غير موجودة.",
        "invalid_role": "دور غير صالح.",
        "invite_not_found": "غير موجود.",
        "invalid_invite_token": "رمز الدعوة غير صالح.",
        "invite_already_accepted": "تم قبول الدعوة مسبقاً.",
        "invite_expired": "انتهت صلاحية الدعوة.",
        "invite_email_mismatch": "بريد المستخدم المسجّل لا يطابق الدعوة.",
        "only_admins_invite_admins": "فقط مسؤولو مساحة العمل يمكنهم دعوة مسؤولين.",
        "project_id_required": "هذا الحقل مطلوب.",
        "project_not_found": "المشروع غير موجود في مساحة العمل.",
        "subtask_needs_parent": "المهام الفرعية تتطلب مهمة رئيسية.",
        "passwords_mismatch": "كلمتا المرور غير متطابقتين.",
    },
}


def normalize_lang(value: str | None) -> str:
    if not value:
        return DEFAULT_LANG
    code = value.strip().lower().replace("_", "-")
    if code.startswith("ar"):
        return "ar"
    if code.startswith("en"):
        return "en"
    # first tag from Accept-Language style "ar-SA,ar;q=0.9,en;q=0.8"
    primary = code.split(",")[0].split(";")[0].strip()
    if primary.startswith("ar"):
        return "ar"
    return DEFAULT_LANG


def resolve_language(request=None) -> str:
    if request is not None:
        explicit = getattr(request, "LANGUAGE_CODE", None)
        if explicit in SUPPORTED:
            return explicit
        lang_param = request.GET.get("lang") if hasattr(request, "GET") else None
        if lang_param:
            return normalize_lang(lang_param)
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "") if hasattr(request, "META") else ""
        if accept:
            return normalize_lang(accept)
    return DEFAULT_LANG


def t(key: str, lang: str | None = None, request=None, **kwargs: Any) -> str:
    """Translate a message key. Falls back to English, then the key itself."""
    code = lang or resolve_language(request)
    if code not in SUPPORTED:
        code = DEFAULT_LANG
    text = MESSAGES.get(code, {}).get(key) or MESSAGES["en"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
