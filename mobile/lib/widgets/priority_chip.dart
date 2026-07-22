import 'package:flutter/material.dart';

class PriorityChip extends StatelessWidget {
  const PriorityChip({super.key, required this.priority});

  final String priority;

  Color get _color {
    switch (priority.toLowerCase()) {
      case 'highest':
      case 'critical':
        return const Color(0xFFB91C1C);
      case 'high':
        return const Color(0xFFDC2626);
      case 'medium':
        return const Color(0xFFD97706);
      case 'low':
        return const Color(0xFF2563EB);
      case 'lowest':
        return const Color(0xFF64748B);
      default:
        return const Color(0xFF64748B);
    }
  }

  IconData get _icon {
    switch (priority.toLowerCase()) {
      case 'highest':
      case 'critical':
      case 'high':
        return Icons.keyboard_double_arrow_up;
      case 'medium':
        return Icons.drag_handle;
      case 'low':
      case 'lowest':
        return Icons.keyboard_double_arrow_down;
      default:
        return Icons.remove;
    }
  }

  @override
  Widget build(BuildContext context) {
    final label = priority.isEmpty
        ? 'medium'
        : priority[0].toUpperCase() + priority.substring(1).toLowerCase();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(_icon, size: 14, color: _color),
          const SizedBox(width: 2),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: _color,
            ),
          ),
        ],
      ),
    );
  }
}
