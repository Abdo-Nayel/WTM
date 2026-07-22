import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/task_provider.dart';
import '../../services/auth_service.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_view.dart';
import '../../widgets/loading_view.dart';
import '../../widgets/priority_chip.dart';
import '../board/task_detail_sheet.dart';

class BacklogScreen extends ConsumerWidget {
  const BacklogScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final backlog = ref.watch(backlogProvider);

    return RefreshIndicator(
      color: AppTheme.teal,
      onRefresh: () => ref.read(backlogProvider.notifier).load(),
      child: backlog.when(
        loading: () => const LoadingView(message: 'Loading backlog…'),
        error: (e, _) => ErrorView(
          message: e is DioException
              ? AuthService.messageFromDio(e)
              : e.toString(),
          onRetry: () => ref.read(backlogProvider.notifier).load(),
        ),
        data: (tasks) {
          if (tasks.isEmpty) {
            return ListView(
              children: const [
                SizedBox(height: 80),
                EmptyState(
                  title: 'Backlog is empty',
                  subtitle:
                      'Tasks marked as backlog appear here until they move to the board.',
                  icon: Icons.inbox_outlined,
                ),
              ],
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            itemCount: tasks.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final task = tasks[index];
              return Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => showTaskDetailSheet(context, task: task),
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.border),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  if (task.issueKey.isNotEmpty)
                                    Text(
                                      task.issueKey,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                        color: AppTheme.teal,
                                      ),
                                    ),
                                  const SizedBox(width: 8),
                                  PriorityChip(priority: task.priority),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Text(
                                task.title,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 15,
                                ),
                              ),
                              if (task.description.isNotEmpty) ...[
                                const SizedBox(height: 4),
                                Text(
                                  task.description,
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
                        if (task.storyPoints != null)
                          Padding(
                            padding: const EdgeInsets.only(left: 8),
                            child: CircleAvatar(
                              radius: 16,
                              backgroundColor: AppTheme.surfaceAlt,
                              child: Text(
                                '${task.storyPoints}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.slate,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
