import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/login_screen.dart';
import '../../features/auth/register_screen.dart';
import '../../features/backlog/backlog_screen.dart';
import '../../features/board/kanban_board_screen.dart';
import '../../features/calendar/team_calendar_screen.dart';
import '../../features/home/home_shell.dart';
import '../../features/projects/projects_screen.dart';
import '../../features/workspaces/workspace_switcher_screen.dart';
import '../../providers/auth_provider.dart';
import '../../providers/workspace_provider.dart';
import '../../widgets/loading_view.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _shellNavigatorKey = GlobalKey<NavigatorState>();

class _AuthRefresh extends ChangeNotifier {
  void ping() => notifyListeners();
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final refresh = _AuthRefresh();
  ref.listen(authProvider, (_, __) => refresh.ping());
  ref.listen(workspaceProvider, (_, __) => refresh.ping());

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/login',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final ws = ref.read(workspaceProvider);
      final loc = state.matchedLocation;

      if (auth.status == AuthStatus.unknown) return null;

      final isAuthRoute = loc == '/login' || loc == '/register';
      final isWorkspaceRoute = loc == '/workspaces';

      if (auth.status == AuthStatus.unauthenticated) {
        return isAuthRoute ? null : '/login';
      }

      // Authenticated
      if (isAuthRoute) {
        return ws.current == null ? '/workspaces' : '/board';
      }

      if (ws.current == null && !isWorkspaceRoute) {
        return '/workspaces';
      }

      if (ws.current != null && isWorkspaceRoute) {
        return '/board';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/workspaces',
        builder: (context, state) => const WorkspaceSwitcherScreen(),
      ),
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => HomeShell(child: child),
        routes: [
          GoRoute(
            path: '/board',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: KanbanBoardScreen(),
            ),
          ),
          GoRoute(
            path: '/backlog',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: BacklogScreen(),
            ),
          ),
          GoRoute(
            path: '/calendar',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: TeamCalendarScreen(),
            ),
          ),
          GoRoute(
            path: '/projects',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProjectsScreen(),
            ),
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(child: Text('Route not found: ${state.error}')),
    ),
  );
});

/// Shown while auth status is resolving.
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(authProvider).status;
    if (status == AuthStatus.unknown) {
      return const Scaffold(body: LoadingView(message: 'Starting WorkTaskMe…'));
    }
    return const SizedBox.shrink();
  }
}
