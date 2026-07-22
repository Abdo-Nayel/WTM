import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../models/board_column.dart';
import '../../models/task.dart';
import '../../providers/project_provider.dart';
import '../../providers/task_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_view.dart';
import '../../widgets/loading_view.dart';
import 'create_task_sheet.dart';
import 'task_card.dart';
import 'task_detail_sheet.dart';

class KanbanBoardScreen extends ConsumerWidget {
  const KanbanBoardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projects = ref.watch(projectProvider);
    final board = ref.watch(boardProvider);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: projects.projects.isEmpty
                    ? Text(
                        projects.isLoading
                            ? 'Loading projects…'
                            : 'No projects — create one in Projects',
                        style: const TextStyle(color: AppTheme.slateMuted),
                      )
                    : DropdownButtonFormField<String>(
                        value: projects.selectedId,
                        decoration: const InputDecoration(
                          labelText: 'Project',
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          isDense: true,
                        ),
                        items: projects.projects
                            .map(
                              (p) => DropdownMenuItem(
                                value: p.id,
                                child: Text('${p.key} — ${p.name}'),
                              ),
                            )
                            .toList(),
                        onChanged: (id) {
                          if (id != null) {
                            ref.read(projectProvider.notifier).select(id);
                          }
                        },
                      ),
              ),
              const SizedBox(width: 8),
              IconButton(
                tooltip: 'Refresh',
                onPressed: () => ref.read(boardProvider.notifier).load(),
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
        ),
        Expanded(child: _BoardBody(board: board)),
      ],
    );
  }
}

class _BoardBody extends ConsumerWidget {
  const _BoardBody({required this.board});

  final BoardState board;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projects = ref.watch(projectProvider);

    if (projects.projects.isEmpty && !projects.isLoading) {
      return EmptyState(
        title: 'No projects',
        subtitle: 'Create a project to open its Kanban board.',
        icon: Icons.view_kanban_outlined,
        actionLabel: 'Go to Projects',
        onAction: () => context.go('/projects'),
      );
    }

    if (board.isLoading && board.data == null) {
      return const LoadingView(message: 'Loading board…');
    }

    if (board.error != null && board.data == null) {
      return ErrorView(
        message: board.error!,
        onRetry: () => ref.read(boardProvider.notifier).load(),
      );
    }

    final data = board.data;
    if (data == null || data.columns.isEmpty) {
      return const EmptyState(
        title: 'Board is empty',
        subtitle: 'This project has no columns yet.',
        icon: Icons.dashboard_customize_outlined,
      );
    }

    return Stack(
      children: [
        RefreshIndicator(
          color: AppTheme.teal,
          onRefresh: () => ref.read(boardProvider.notifier).load(),
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(12, 4, 12, 88),
            children: [
              for (final col in data.columns)
                _KanbanColumn(
                  column: col,
                  tasks: data.tasks
                      .where((t) => t.columnId == col.id && !t.isInBacklog)
                      .toList()
                    ..sort((a, b) => a.boardPosition.compareTo(b.boardPosition)),
                ),
            ],
          ),
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            heroTag: 'create_task',
            onPressed: projects.selectedId == null
                ? null
                : () => showCreateTaskSheet(
                      context,
                      projectId: projects.selectedId!,
                      columns: data.columns,
                    ),
            icon: const Icon(Icons.add),
            label: const Text('Task'),
          ),
        ),
      ],
    );
  }
}

class _KanbanColumn extends ConsumerWidget {
  const _KanbanColumn({
    required this.column,
    required this.tasks,
  });

  final BoardColumn column;
  final List<Task> tasks;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DragTarget<Task>(
      onWillAcceptWithDetails: (details) => details.data.columnId != column.id,
      onAcceptWithDetails: (details) async {
        final task = details.data;
        final ok = await ref.read(boardProvider.notifier).moveTask(
              taskId: task.id,
              columnId: column.id,
              boardPosition: tasks.length,
            );
        if (!context.mounted) return;
        if (!ok) {
          final err = ref.read(boardProvider).error ?? 'Move failed';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(err), backgroundColor: AppTheme.danger),
          );
        }
      },
      builder: (context, candidate, rejected) {
        final hovering = candidate.isNotEmpty;
        return Container(
          width: 288,
          margin: const EdgeInsets.symmetric(horizontal: 6),
          decoration: BoxDecoration(
            color: hovering
                ? AppTheme.teal.withOpacity(0.06)
                : AppTheme.surfaceAlt,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: hovering ? AppTheme.teal : AppTheme.border,
              width: hovering ? 1.5 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 14, 14, 8),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        column.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '${tasks.length}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.slateMuted,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(10, 4, 10, 12),
                  itemCount: tasks.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final task = tasks[index];
                    return LongPressDraggable<Task>(
                      data: task,
                      feedback: Material(
                        color: Colors.transparent,
                        child: Transform.rotate(
                          angle: -0.02,
                          child: TaskCard(task: task, isDragging: true),
                        ),
                      ),
                      childWhenDragging: Opacity(
                        opacity: 0.35,
                        child: TaskCard(task: task),
                      ),
                      child: TaskCard(
                        task: task,
                        onTap: () => showTaskDetailSheet(context, task: task),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
