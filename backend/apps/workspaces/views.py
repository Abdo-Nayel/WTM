from django.conf import settings

from django.core.mail import send_mail

from django.db.models import Count, Q

from django.utils import timezone

from rest_framework import status, viewsets

from rest_framework.decorators import action

from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.response import Response

from rest_framework.views import APIView



from apps.core.i18n import t

from apps.core.permissions import IsAuthenticatedAndActive, has_min_role

from apps.projects.models import BoardColumn, Project

from apps.tasks.models import Task

from apps.workspaces.models import (

    Workspace,

    WorkspaceInvitation,

    WorkspaceMembership,

    WorkspaceRole,

)

from apps.workspaces.serializers import (

    AcceptInviteSerializer,

    InviteCreateSerializer,

    WorkspaceCreateSerializer,

    WorkspaceInvitationSerializer,

    WorkspaceMembershipSerializer,

    WorkspaceSerializer,

)





class WorkspaceViewSet(viewsets.ModelViewSet):

    """

    List/create workspaces for the current user.

    Does NOT require X-Workspace-Id (user may have many workspaces).

    """



    permission_classes = [IsAuthenticatedAndActive]



    def get_serializer_class(self):

        if self.action == "create":

            return WorkspaceCreateSerializer

        return WorkspaceSerializer



    def get_queryset(self):

        return (

            Workspace.objects.filter(

                memberships__user=self.request.user,

                memberships__is_active=True,

                is_active=True,

            )

            .distinct()

            .select_related("owner")

        )



    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        workspace = serializer.save()

        return Response(

            WorkspaceSerializer(workspace, context={"request": request}).data,

            status=status.HTTP_201_CREATED,

        )



    @action(detail=True, methods=["get"], url_path="stats")

    def stats(self, request, pk=None):

        workspace = self.get_object()

        from apps.core.models import Notification



        projects = Project.objects.filter(workspace=workspace, is_archived=False).count()

        tasks_qs = Task.objects.filter(workspace=workspace)

        task_counts = tasks_qs.aggregate(

            tasks=Count("id"),

            backlog=Count("id", filter=Q(is_in_backlog=True)),

            done=Count(

                "id",

                filter=Q(column__category=BoardColumn.ColumnCategory.DONE),

            ),

        )

        members = workspace.memberships.filter(is_active=True).count()

        unread = Notification.objects.filter(

            workspace=workspace,

            user=request.user,

            is_read=False,

        ).count()

        return Response(

            {

                "projects": projects,

                "tasks": task_counts["tasks"],

                "backlog": task_counts["backlog"],

                "done": task_counts["done"],

                "members": members,

                "unread_notifications": unread,

            }

        )



    @action(detail=True, methods=["get", "patch"], url_path="members")

    def members(self, request, pk=None):

        workspace = self.get_object()

        lang = getattr(request, "LANGUAGE_CODE", None)

        if request.method == "GET":

            qs = workspace.memberships.filter(is_active=True).select_related("user")

            return Response(WorkspaceMembershipSerializer(qs, many=True).data)



        # PATCH: update member role (admin only)

        membership = workspace.memberships.filter(

            user=request.user, is_active=True

        ).first()

        if not has_min_role(membership, WorkspaceRole.ADMIN):

            return Response({"detail": t("admin_required", lang=lang)}, status=403)



        target_id = request.data.get("membership_id")

        new_role = request.data.get("role")

        try:

            target = workspace.memberships.get(pk=target_id)

        except WorkspaceMembership.DoesNotExist:

            return Response(

                {"detail": t("membership_not_found", lang=lang)}, status=404

            )

        if new_role not in WorkspaceRole.values:

            return Response({"detail": t("invalid_role", lang=lang)}, status=400)

        target.role = new_role

        target.save(update_fields=["role", "updated_at"])

        return Response(WorkspaceMembershipSerializer(target).data)



    @action(detail=True, methods=["get"], url_path="invitations")

    def invitations(self, request, pk=None):

        """List pending invitations (admins only)."""

        workspace = self.get_object()

        lang = getattr(request, "LANGUAGE_CODE", None)

        membership = workspace.memberships.filter(

            user=request.user, is_active=True

        ).first()

        if not has_min_role(membership, WorkspaceRole.ADMIN):

            return Response({"detail": t("admin_required", lang=lang)}, status=403)



        qs = (

            workspace.invitations.filter(accepted_at__isnull=True)

            .filter(expires_at__gt=timezone.now())

            .select_related("invited_by")

            .order_by("-created_at")

        )

        return Response(WorkspaceInvitationSerializer(qs, many=True).data)



    @action(detail=True, methods=["post"], url_path="invite")

    def invite(self, request, pk=None):

        workspace = self.get_object()

        lang = getattr(request, "LANGUAGE_CODE", None)

        membership = workspace.memberships.filter(

            user=request.user, is_active=True

        ).first()

        if not has_min_role(membership, WorkspaceRole.ADMIN):

            return Response(

                {"detail": t("admin_required_invite", lang=lang)}, status=403

            )



        ser = InviteCreateSerializer(

            data=request.data, context={"membership": membership, "request": request}

        )

        ser.is_valid(raise_exception=True)

        invite = WorkspaceInvitation.create_invite(

            workspace=workspace,

            email=ser.validated_data["email"],

            role=ser.validated_data["role"],

            invited_by=request.user,

        )

        invite_url = f"{settings.FRONTEND_URL}/?invite={invite.token}"

        mail_body = (

            f"{request.user.full_name} invited you to join "

            f"{workspace.name} as {invite.get_role_display()}.\n\n"

            f"1) Create an account (or sign in) with: {invite.email}\n"

            f"2) Open this link to accept:\n{invite_url}\n"

        )

        sent = send_mail(

            subject=f"You're invited to {workspace.name} on WorkTaskMe",

            message=mail_body,

            from_email=settings.DEFAULT_FROM_EMAIL,

            recipient_list=[invite.email],

            fail_silently=True,

        )

        # Dev convenience: always print invite link to server console

        print(f"\n[WorkTaskMe INVITE] to={invite.email} sent={bool(sent)}\n{invite_url}\n")



        from apps.accounts.models import User

        from apps.core.models import Notification

        from apps.core.notify import notify



        existing = User.objects.filter(email__iexact=invite.email).first()

        if existing:

            notify(

                workspace=workspace,

                user=existing,

                kind=Notification.Kind.INVITE,

                title=f"Invitation to {workspace.name}",

                body=f"You were invited as {invite.role}. Open the invite link to join.",

                link=invite_url,

                meta={"token": invite.token},

            )



        data = WorkspaceInvitationSerializer(invite).data

        data["email_sent"] = bool(sent)

        data["dev_note"] = (

            "In local DEBUG, email prints to the Django console. "

            "Use invite_url below to accept."

        )

        return Response(data, status=status.HTTP_201_CREATED)





class AcceptInviteView(APIView):

    permission_classes = [IsAuthenticated]



    def post(self, request):

        serializer = AcceptInviteSerializer(

            data=request.data, context={"request": request}

        )

        serializer.is_valid(raise_exception=True)

        membership = serializer.save()

        return Response(

            {

                "workspace": WorkspaceSerializer(

                    membership.workspace, context={"request": request}

                ).data,

                "membership": WorkspaceMembershipSerializer(membership).data,

            },

            status=status.HTTP_200_OK,

        )





class InvitePreviewView(APIView):

    """Public preview of an invite (email + workspace name) before login."""



    permission_classes = [AllowAny]



    def get(self, request, token):

        lang = getattr(request, "LANGUAGE_CODE", None)

        try:

            invite = WorkspaceInvitation.objects.select_related("workspace").get(

                token=token

            )

        except WorkspaceInvitation.DoesNotExist:

            return Response(

                {"detail": t("invite_not_found", lang=lang)}, status=404

            )

        return Response(

            {

                "email": invite.email,

                "role": invite.role,

                "workspace_name": invite.workspace.name,

                "expired": invite.is_expired,

                "accepted": invite.is_accepted,

            }

        )


