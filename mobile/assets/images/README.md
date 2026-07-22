# WorkTaskMe image assets

## Brand files

| File | Use |
|------|-----|
| `worktaskme-icon.svg` | Vector app mark (W → arrow + check) |
| `worktaskme-logo.svg` | Horizontal lockup (icon + wordmark) |
| `app_icon.png` | 1024×1024 launcher source for `flutter_launcher_icons` |
| `splash_logo.png` | Native splash mark |

Canonical copies also live at the repo root: `../../assets/images/`.

## Generate phone icons / splash

```bash
cd mobile
flutter pub get
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

Brand colors: Indigo `#4F46E5`, Emerald `#10B981`.
