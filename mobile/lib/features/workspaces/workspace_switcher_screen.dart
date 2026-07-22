import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/workspace_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_view.dart';
import '../../widgets/loading_view.dart';
import 'create_workspace_sheet.dart';

class WorkspaceSwitcherScreen extends ConsumerWidget {
  const WorkspaceSwitcherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(workspaceProvider);
    final user = ref.watch(authProvider).user;

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: const Text('WorkTaskMe'),
        actions: [
          if (user != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Text(
                  user.displayName,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppTheme.slateMuted,
                  ),
                ),
              ),
            ),
          IconButton(
            tooltip: 'Sign out',
            onPressed: () => ref.read(authProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.teal,
        onRefresh: () => ref.read(workspaceProvider.notifier).load(),
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(24, 16, 24, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Choose a workspace',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Workspaces keep projects, boards, and calendars separate.',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.slateMuted,
                          ),
                    ),
                  ],
                ),
              ),
            ),
            if (state.isLoading && state.workspaces.isEmpty)
              const SliverFillRemaining(child: LoadingView())
            else if (state.error != null && state.workspaces.isEmpty)
              SliverFillRemaining(
                child: ErrorView(
                  message: state.error!,
                  onRetry: () => ref.read(workspaceProvider.notifier).load(),
                ),
              )
            else if (state.workspaces.isEmpty)
              SliverFillRemaining(
                child: EmptyState(
                  title: 'No workspaces yet',
                  subtitle: 'Create your first workspace to get started.',
                  icon: Icons.business_outlined,
                  actionLabel: 'Create workspace',
                  onAction: () => showCreateWorkspaceSheet(context),
                ),
              )
            else
              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverList.separated(
                  itemCount: state.workspaces.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final ws = state.workspaces[index];
                    return Material(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () async {
                          await ref
                              .read(workspaceProvider.notifier)
                              .select(ws);
                        },
                        child: Container(
                          padding: const EdgeInsets.all(18),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.border),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 48,
                                height: 48,
                                decoration: BoxDecoration(
                                  color: AppTheme.teal.withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  ws.name.isNotEmpty
                                      ? ws.name[0].toUpperCase()
                                      : 'W',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    fontSize: 20,
                                    color: AppTheme.teal,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      ws.name,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 16,
                                      ),
                                    ),
                                    if (ws.description.isNotEmpty) ...[
                                      const SizedBox(height: 4),
                                      Text(
                                        ws.description,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          color: AppTheme.slateMuted,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ],
                                    const SizedBox(height: 4),
                                    Text(
                                      'Key prefix: ${ws.defaultKeyPrefix}',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.slateMuted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(
                                Icons.chevron_right,
                                color: AppTheme.slateMuted,
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => showCreateWorkspaceSheet(context),
        icon: const Icon(Icons.add),
        label: const Text('New workspace'),
      ),
    );
  }
}
