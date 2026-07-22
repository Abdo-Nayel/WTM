# WorkTaskMe — Django Backend

Jira-style task management + TeamUp-style calendar in a **single PostgreSQL database** with workspace-level isolation (`workspace_id` + membership RBAC).

## Stack

- Django 5 + Django REST Framework
- SimpleJWT (access + refresh)
- PostgreSQL + `workspace_id` multi-tenancy
- Django Channels (WebSocket board/calendar updates)
- drf-spectacular (OpenAPI at `/api/docs/`)

## Quick start (local)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

### Option A — SQLite (fastest bootstrap)

In `.env` set:

```
USE_SQLITE=True
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Option B — Docker (Postgres + Redis)

```bash
copy .env.example .env
docker compose up --build
```

API: `http://localhost:8000`  
Swagger: `http://localhost:8000/api/docs/`

## Multi-tenant contract

Every tenant-owned request (projects, tasks, calendar, …) **must** send:

```
Authorization: Bearer <access_token>
X-Workspace-Id: <workspace_uuid>
```

Isolation layers:

1. **Schema** — all domain tables have `workspace_id` FK (`TenantModel`)
2. **ORM** — `TenantManager.for_workspace(ws)`
3. **HTTP** — `WorkspaceTenantMiddleware` reads `X-Workspace-Id`
4. **RBAC** — `HasWorkspaceRole` / `TenantViewSetMixin` (admin → project_manager → member → viewer)
5. **Realtime** — WebSocket consumers verify membership before joining a group

## Auth & workspace flow

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/auth/register/` | Create user |
| POST | `/api/auth/token/` | JWT login (`email` + `password`) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PATCH | `/api/auth/me/` | Current user |
| POST | `/api/workspaces/` | Create workspace (caller becomes admin) |
| GET | `/api/workspaces/` | List my workspaces |
| POST | `/api/workspaces/{id}/invite/` | Email invite (admin) |
| POST | `/api/workspaces/invitations/accept/` | `{ "token": "..." }` |

## Domain APIs (require `X-Workspace-Id`)

| Resource | Base path |
|----------|-----------|
| Projects + board | `/api/projects/` , `/api/projects/{id}/board/` |
| Epics / Labels / Columns | `/api/projects/epics/` , `.../labels/` , `.../columns/` |
| Tasks | `/api/tasks/` |
| Backlog | `/api/tasks/backlog/` |
| Kanban move | `POST /api/tasks/{id}/move/` |
| Calendar | `/api/calendar/events/` |
| Resource timeline | `/api/calendar/events/timeline/` |

### Example: create project → task → move on board

```http
POST /api/projects/
X-Workspace-Id: <ws>
{ "name": "Platform", "key": "WTM", "description": "Core" }

POST /api/tasks/
X-Workspace-Id: <ws>
{
  "project_id": "<project_uuid>",
  "title": "Set up CI",
  "task_type": "task",
  "priority": "high",
  "story_points": 3,
  "due_date": "2026-07-30"
}

POST /api/tasks/<task_id>/move/
X-Workspace-Id: <ws>
{ "column_id": "<column_uuid>", "board_position": 1.0, "is_in_backlog": false }
```

Task due dates auto-create / update `CalendarEvent` rows (`source=task`).

## WebSockets

```
ws://localhost:8000/ws/workspace/<workspace_id>/board/
ws://localhost:8000/ws/workspace/<workspace_id>/calendar/
```

## Project layout

```
backend/
  config/           # settings, urls, asgi/wsgi
  apps/
    core/           # TenantModel, middleware, permissions, channels
    accounts/       # User + JWT register/me
    workspaces/     # Workspace, membership, invites, RBAC roles
    projects/       # Project, Epic, Label, BoardColumn
    tasks/          # Task, comments, activity, calendar sync signals
    calendar_events/# TeamUp-style events + timeline
```

## Roles

| Role | Capabilities |
|------|----------------|
| `admin` | Invites, billing-ready, full control |
| `project_manager` | Projects, columns, archive |
| `member` | Create/edit tasks & calendar events |
| `viewer` | Read-only |

## Next step

Flutter client (Step 2): JWT client + `X-Workspace-Id` header, Kanban board, TeamUp calendar.
