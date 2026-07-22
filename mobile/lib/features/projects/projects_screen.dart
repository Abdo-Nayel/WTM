import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/project_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_view.dart';
import '../../widgets/loading_view.dart';
import 'create_project_sheet.dart';

class ProjectsScreen extends ConsumerWidget {
  const ProjectsScreen({super.key});

  Color _parseColor(String hex) {
    var h = hex.replaceAll('#', '');
    if (h.length == 6) h = 'FF$h';
    final value = int.tryParse(h, radix: 16);
    if (value == null) return AppTheme.teal;
    return Color(value);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(projectProvider);

    return Stack(
      children: [
        RefreshIndicator(
          color: AppTheme.teal,
          onRefresh: () => ref.read(projectProvider.notifier).load(),
          child: state.isLoading && state.projects.isEmpty
              ? const LoadingView(message: 'Loading projects…')
              : state.error != null && state.projects.isEmpty
                  ? ErrorView(
                      message: state.error!,
                      onRetry: () =>
                          ref.read(projectProvider.notifier).load(),
                    )
                  : state.projects.isEmpty
                      ? ListView(
                          children: [
                            const SizedBox(height: 60),
                            EmptyState(
                              title: 'No projects',
                              subtitle:
                                  'Create a project to get a Kanban board with default columns.',
                              icon: Icons.folder_open_outlined,
                              actionLabel: 'Create project',
                              onAction: () => showCreateProjectSheet(context),
                            ),
                          ],
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
                          itemCount: state.projects.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final p = state.projects[index];
                            final selected = p.id == state.selectedId;
                            final color = _parseColor(p.color);
                            return Material(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(12),
                                onTap: () {
                                  ref
                                      .read(projectProvider.notifier)
                                      .select(p.id);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        'Selected ${p.name} for the board',
                                      ),
                                      duration: const Duration(seconds: 1),
                                    ),
                                  );
                                },
                                child: Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: selected
                                          ? AppTheme.teal
                                          : AppTheme.border,
                                      width: selected ? 1.5 : 1,
                                    ),
                                  ),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 44,
                                        height: 44,
                                        decoration: BoxDecoration(
                                          color: color.withOpacity(0.15),
                                          borderRadius:
                                              BorderRadius.circular(10),
                                        ),
                                        alignment: Alignment.center,
                                        child: Text(
                                          p.key.length > 3
                                              ? p.key.substring(0, 3)
                                              : p.key,
                                          style: TextStyle(
                                            fontWeight: FontWeight.w800,
                                            color: color,
                                            fontSize: 12,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 14),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              p.name,
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                                fontSize: 16,
                                              ),
                                            ),
                                            const SizedBox(height: 2),
                                            Text(
                                              p.key,
                                              style: const TextStyle(
                                                color: AppTheme.slateMuted,
                                                fontSize: 13,
                                              ),
                                            ),
                                            if (p.description.isNotEmpty) ...[
                                              const SizedBox(height: 4),
                                              Text(
                                                p.description,
                                                maxLines: 2,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  color: AppTheme.slateMuted,
                                                  fontSize: 13,
                                                ),
                                              ),
                                            ],
                                          ],
                                        ),
                                      ),
                                      if (selected)
                                        const Icon(
                                          Icons.check_circle,
                                          color: AppTheme.teal,
                                        ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            heroTag: 'create_project',
            onPressed: () => showCreateProjectSheet(context),
            icon: const Icon(Icons.add),
            label: const Text('Project'),
          ),
        ),
      ],
    );
  }
}
