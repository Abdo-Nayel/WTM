# WorkTaskMe Mobile

Flutter client for **WorkTaskMe** — Agile Kanban boards plus a shared team calendar.

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

Default (release): `https://worktaskme.com`

Override for local/emulator:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Google Play (Android release)

1. Create upload keystore (once):

```powershell
cd mobile\android
.\create_keystore.ps1
```

2. Build the Play Bundle:

```powershell
cd mobile
flutter pub get
flutter build appbundle --release
```

Output: `build/app/outputs/bundle/release/app-release.aab`

Application id: `com.lyomastech.worktaskme`

3. In Play Console → Create app → Internal testing / Production → upload the `.aab`.

**Never commit** `android/key.properties` or `android/upload-keystore.jks`.

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
