class CalendarEvent {
  const CalendarEvent({
    required this.id,
    required this.title,
    required this.startAt,
    required this.endAt,
    this.allDay = false,
    this.color = '#0F766E',
    this.projectId,
    this.assigneeId,
    this.department,
    this.description = '',
  });

  final String id;
  final String title;
  final DateTime startAt;
  final DateTime endAt;
  final bool allDay;
  final String color;
  final String? projectId;
  final String? assigneeId;
  final String? department;
  final String description;

  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    final start = DateTime.tryParse(json['start_at']?.toString() ?? '') ??
        DateTime.now();
    final end = DateTime.tryParse(json['end_at']?.toString() ?? '') ??
        start.add(const Duration(hours: 1));

    return CalendarEvent(
      id: (json['id'] ?? '').toString(),
      title: json['title'] as String? ?? '',
      startAt: start,
      endAt: end,
      allDay: json['all_day'] == true,
      color: json['color'] as String? ?? '#0F766E',
      projectId: json['project_id']?.toString() ?? json['project']?.toString(),
      assigneeId:
          json['assignee_id']?.toString() ?? json['assignee']?.toString(),
      department: json['department'] as String?,
      description: json['description'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'start_at': startAt.toIso8601String(),
        'end_at': endAt.toIso8601String(),
        'all_day': allDay,
        'color': color,
        if (projectId != null) 'project_id': projectId,
        if (assigneeId != null) 'assignee_id': assigneeId,
        if (department != null) 'department': department,
        if (description.isNotEmpty) 'description': description,
      };
}
