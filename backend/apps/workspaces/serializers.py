from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.core.i18n import t
from apps.workspaces.models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
    WorkspaceRole,
)


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    my_role = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "owner",
            "is_active",
            "default_key_prefix",
            "my_role",
            "member_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "slug", "created_at", "updated_at")

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        m = obj.memberships.filter(user=request.user, is_active=True).first()
        return m.role if m else None

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ("name", "description", "default_key_prefix")

    def create(self, validated_data):
        user = self.context["request"].user
        base_slug = slugify(validated_data["name"])[:60] or "workspace"
        slug = base_slug
        n = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{n}"
            n += 1
        workspace = Workspace.objects.create(owner=user, slug=slug, **validated_data)
        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceRole.ADMIN,
        )
        return workspace


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = WorkspaceMembership
        fields = (
            "id",
            "workspace",
            "user",
            "user_id",
            "role",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "workspace", "user", "created_at")


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    invite_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceInvitation
        fields = (
            "id",
            "workspace",
            "email",
            "role",
            "token",
            "invited_by",
            "accepted_at",
            "expires_at",
            "invite_url",
            "created_at",
        )
        read_only_fields = (
            "id",
            "workspace",
            "token",
            "invited_by",
            "accepted_at",
            "expires_at",
            "created_at",
        )

    def get_invite_url(self, obj):
        from django.conf import settings

        return f"{settings.FRONTEND_URL}/?invite={obj.token}"


class InviteCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=WorkspaceRole.choices, default=WorkspaceRole.MEMBER
    )

    def validate_role(self, value):
        if value == WorkspaceRole.ADMIN:
            membership = self.context.get("membership")
            if membership is None or membership.role != WorkspaceRole.ADMIN:
                request = self.context.get("request")
                raise serializers.ValidationError(
                    t("only_admins_invite_admins", request=request)
                )
        return value


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField()

    def _lang_request(self):
        return self.context.get("request")

    def validate_token(self, value):
        request = self._lang_request()
        try:
            invite = WorkspaceInvitation.objects.select_related(
                "workspace", "invited_by"
            ).get(token=value)
        except WorkspaceInvitation.DoesNotExist as exc:
            raise serializers.ValidationError(
                t("invalid_invite_token", request=request)
            ) from exc
        if invite.is_accepted:
            raise serializers.ValidationError(
                t("invite_already_accepted", request=request)
            )
        if invite.is_expired:
            raise serializers.ValidationError(t("invite_expired", request=request))
        self.context["invite"] = invite
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        invite = self.context["invite"]
        request = self._lang_request()
        if user.email.lower() != invite.email.lower():
            raise serializers.ValidationError(
                {"email": t("invite_email_mismatch", request=request)}
            )
        membership, _ = WorkspaceMembership.objects.update_or_create(
            workspace=invite.workspace,
            user=user,
            defaults={
                "role": invite.role,
                "is_active": True,
                "invited_by": invite.invited_by,
            },
        )
        invite.accepted_at = timezone.now()
        invite.save(update_fields=["accepted_at"])

        # Notify the inviter that their invite was accepted
        if invite.invited_by_id and invite.invited_by_id != user.id:
            from apps.core.models import Notification
            from apps.core.notify import notify

            notify(
                workspace=invite.workspace,
                user=invite.invited_by,
                kind=Notification.Kind.INVITE,
                title=f"{user.full_name} joined {invite.workspace.name}",
                body=f"{user.email} accepted your invitation as {invite.role}.",
                link=f"/workspaces/{invite.workspace_id}",
                meta={
                    "invite_id": str(invite.id),
                    "new_member_id": str(user.id),
                },
            )
        return membership
