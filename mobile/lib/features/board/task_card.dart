import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../models/task.dart';
import '../../widgets/priority_chip.dart';

class TaskCard extends StatelessWidget {
  const TaskCard({
    super.key,
    required this.task,
    this.onTap,
    this.isDragging = false,
  });

  final Task task;
  final VoidCallback? onTap;
  final bool isDragging;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: isDragging ? Colors.white.withOpacity(0.95) : Colors.white,
      elevation: isDragging ? 6 : 0,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          width: 260,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: isDragging ? AppTheme.teal : AppTheme.border,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (task.issueKey.isNotEmpty)
                    Text(
                      task.issueKey,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.slateMuted,
                      ),
                    ),
                  const Spacer(),
                  PriorityChip(priority: task.priority),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                task.title,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  _TypeBadge(type: task.taskType),
                  if (task.storyPoints != null) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.surfaceAlt,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '${task.storyPoints} SP',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.slate,
                        ),
                      ),
                    ),
                  ],
                  const Spacer(),
                  if (task.assignee != null)
                    CircleAvatar(
                      radius: 12,
                      backgroundColor: AppTheme.teal.withOpacity(0.15),
                      child: Text(
                        task.assignee!.initials,
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.teal,
                        ),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TypeBadge extends StatelessWidget {
  const _TypeBadge({required this.type});

  final String type;

  @override
  Widget build(BuildContext context) {
    final t = type.toLowerCase();
    IconData icon;
    Color color;
    switch (t) {
      case 'bug':
        icon = Icons.bug_report_outlined;
        color = const Color(0xFFDC2626);
      case 'story':
        icon = Icons.bookmark_border;
        color = const Color(0xFF059669);
      case 'epic':
        icon = Icons.flash_on_outlined;
        color = const Color(0xFF7C3AED);
      default:
        icon = Icons.check_box_outlined;
        color = AppTheme.teal;
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(
          t.isEmpty ? 'task' : t,
          style: TextStyle(
            fontSize: 11,
            color: color,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
