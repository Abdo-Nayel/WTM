# WorkTaskMe Mobile

Flutter client for **WorkTaskMe** — Jira-style Kanban boards plus TeamUp-style team calendar.

## Prerequisites

- Flutter SDK 3.16+ (`flutter --version`)
- Django backend running at `http://127.0.0.1:8000`

## Setup

```bash
cd mobile
flutter pub get
```

## Run

```bash
# Chrome (web)
flutter run -d chrome

# Android emulator / device
flutter run

# iOS simulator (macOS)
flutter run -d ios
```

## API base URL

Default: `http://127.0.0.1:8000`  
Change in `lib/core/config/api_config.dart` if needed.

For Android emulator, use `http://10.0.2.2:8000` instead of `127.0.0.1`.

## App flow

1. Register / Login
2. Create or select a workspace
3. Home shell with tabs: **Board** · **Backlog** · **Calendar** · **Projects**

## Features

- JWT auth with automatic token refresh
- Workspace-scoped API calls (`X-Workspace-Id`)
- Kanban board with drag-and-drop between columns
- Backlog list
- Month/week team calendar
- Project management
