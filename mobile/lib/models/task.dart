import 'board_column.dart';
import 'user.dart';

class Task {
  const Task({
    required this.id,
    required this.title,
    this.description = '',
    this.issueKey = '',
    this.taskType = 'task',
    this.priority = 'medium',
    this.storyPoints,
    this.dueDate,
    this.assignee,
    this.assigneeId,
    this.columnId,
    this.projectId,
    this.boardPosition = 0,
    this.isInBacklog = false,
    this.status,
  });

  final String id;
  final String title;
  final String description;
  final String issueKey;
  final String taskType;
  final String priority;
  final int? storyPoints;
  final DateTime? dueDate;
  final User? assignee;
  final String? assigneeId;
  final String? columnId;
  final String? projectId;
  final int boardPosition;
  final bool isInBacklog;
  final String? status;

  factory Task.fromJson(Map<String, dynamic> json) {
    User? assignee;
    if (json['assignee'] is Map<String, dynamic>) {
      assignee = User.fromJson(json['assignee'] as Map<String, dynamic>);
    }

    DateTime? due;
    final dueRaw = json['due_date'];
    if (dueRaw is String && dueRaw.isNotEmpty) {
      due = DateTime.tryParse(dueRaw);
    }

    return Task(
      id: (json['id'] ?? '').toString(),
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      issueKey: json['issue_key'] as String? ?? json['key'] as String? ?? '',
      taskType: json['task_type'] as String? ?? 'task',
      priority: json['priority'] as String? ?? 'medium',
      storyPoints: json['story_points'] is int
          ? json['story_points'] as int
          : int.tryParse('${json['story_points'] ?? ''}'),
      dueDate: due,
      assignee: assignee,
      assigneeId: json['assignee_id']?.toString() ??
          assignee?.id ??
          (json['assignee'] is String ? json['assignee'] as String : null),
      columnId: json['column_id']?.toString() ?? json['column']?.toString(),
      projectId: json['project_id']?.toString() ?? json['project']?.toString(),
      boardPosition: json['board_position'] is int
          ? json['board_position'] as int
          : int.tryParse('${json['board_position'] ?? 0}') ?? 0,
      isInBacklog: json['is_in_backlog'] == true,
      status: json['status'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'description': description,
        'issue_key': issueKey,
        'task_type': taskType,
        'priority': priority,
        if (storyPoints != null) 'story_points': storyPoints,
        if (dueDate != null)
          'due_date': dueDate!.toIso8601String().split('T').first,
        if (assigneeId != null) 'assignee_id': assigneeId,
        if (columnId != null) 'column_id': columnId,
        if (projectId != null) 'project_id': projectId,
        'board_position': boardPosition,
        'is_in_backlog': isInBacklog,
      };

  Task copyWith({
    String? id,
    String? title,
    String? description,
    String? issueKey,
    String? taskType,
    String? priority,
    int? storyPoints,
    DateTime? dueDate,
    User? assignee,
    String? assigneeId,
    String? columnId,
    String? projectId,
    int? boardPosition,
    bool? isInBacklog,
    String? status,
  }) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      issueKey: issueKey ?? this.issueKey,
      taskType: taskType ?? this.taskType,
      priority: priority ?? this.priority,
      storyPoints: storyPoints ?? this.storyPoints,
      dueDate: dueDate ?? this.dueDate,
      assignee: assignee ?? this.assignee,
      assigneeId: assigneeId ?? this.assigneeId,
      columnId: columnId ?? this.columnId,
      projectId: projectId ?? this.projectId,
      boardPosition: boardPosition ?? this.boardPosition,
      isInBacklog: isInBacklog ?? this.isInBacklog,
      status: status ?? this.status,
    );
  }
}

class BoardData {
  const BoardData({
    required this.project,
    required this.columns,
    required this.tasks,
  });

  final Map<String, dynamic> project;
  final List<BoardColumn> columns;
  final List<Task> tasks;

  factory BoardData.fromJson(Map<String, dynamic> json) {
    final cols = <BoardColumn>[];
    final rawCols = json['columns'];
    if (rawCols is List) {
      for (final c in rawCols) {
        if (c is Map<String, dynamic>) {
          cols.add(BoardColumn.fromJson(c));
        }
      }
    }
    cols.sort((a, b) => a.position.compareTo(b.position));

    final tasks = <Task>[];
    final rawTasks = json['tasks'];
    if (rawTasks is List) {
      for (final t in rawTasks) {
        if (t is Map<String, dynamic>) {
          tasks.add(Task.fromJson(t));
        }
      }
    }

    return BoardData(
      project: json['project'] is Map<String, dynamic>
          ? json['project'] as Map<String, dynamic>
          : {},
      columns: cols,
      tasks: tasks,
    );
  }
}
