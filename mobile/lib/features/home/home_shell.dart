import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/workspace_provider.dart';

class HomeShell extends ConsumerWidget {
  const HomeShell({super.key, required this.child});

  final Widget child;

  int _indexForLocation(String location) {
    if (location.startsWith('/backlog')) return 1;
    if (location.startsWith('/calendar')) return 2;
    if (location.startsWith('/projects')) return 3;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = _indexForLocation(location);
    final workspace = ref.watch(workspaceProvider).current;
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'WorkTaskMe',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.tealDark,
                letterSpacing: -0.4,
              ),
            ),
            if (workspace != null)
              Text(
                workspace.name,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: AppTheme.slateMuted,
                ),
              ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            tooltip: 'Account',
            icon: CircleAvatar(
              radius: 16,
              backgroundColor: AppTheme.teal.withOpacity(0.15),
              child: Text(
                user?.initials ?? '?',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.teal,
                ),
              ),
            ),
            onSelected: (value) async {
              if (value == 'switch') {
                await ref.read(workspaceProvider.notifier).clearSelection();
              } else if (value == 'logout') {
                await ref.read(authProvider.notifier).logout();
              }
            },
            itemBuilder: (context) => [
              if (user != null)
                PopupMenuItem(
                  enabled: false,
                  child: Text(
                    user.email,
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'switch',
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.swap_horiz),
                  title: Text('Switch workspace'),
                ),
              ),
              const PopupMenuItem(
                value: 'logout',
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.logout),
                  title: Text('Sign out'),
                ),
              ),
            ],
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) {
          switch (i) {
            case 0:
              context.go('/board');
            case 1:
              context.go('/backlog');
            case 2:
              context.go('/calendar');
            case 3:
              context.go('/projects');
          }
        },
        indicatorColor: AppTheme.teal.withOpacity(0.15),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.view_kanban_outlined),
            selectedIcon: Icon(Icons.view_kanban),
            label: 'Board',
          ),
          NavigationDestination(
            icon: Icon(Icons.list_alt_outlined),
            selectedIcon: Icon(Icons.list_alt),
            label: 'Backlog',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month),
            label: 'Calendar',
          ),
          NavigationDestination(
            icon: Icon(Icons.folder_outlined),
            selectedIcon: Icon(Icons.folder),
            label: 'Projects',
          ),
        ],
      ),
    );
  }
}
