import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/task.dart';

class TaskService {
  TaskService(this._client);

  final ApiClient _client;

  Future<List<Task>> list() async {
    final res = await _client.dio.get(ApiConfig.tasks);
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(Task.fromJson)
        .toList();
  }

  Future<List<Task>> backlog() async {
    final res = await _client.dio.get(ApiConfig.tasksBacklog);
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(Task.fromJson)
        .toList();
  }

  Future<Task> create({
    required String projectId,
    required String title,
    String? description,
    String? taskType,
    String? priority,
    int? storyPoints,
    String? dueDate,
    String? assigneeId,
    String? columnId,
  }) async {
    final body = <String, dynamic>{
      'project_id': projectId,
      'title': title,
      if (description != null) 'description': description,
      if (taskType != null) 'task_type': taskType,
      if (priority != null) 'priority': priority,
      if (storyPoints != null) 'story_points': storyPoints,
      if (dueDate != null) 'due_date': dueDate,
      if (assigneeId != null) 'assignee_id': assigneeId,
      if (columnId != null) 'column_id': columnId,
    };
    final res = await _client.dio.post(ApiConfig.tasks, data: body);
    return Task.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Task> move(
    String taskId, {
    String? columnId,
    int? boardPosition,
    bool? isInBacklog,
  }) async {
    final body = <String, dynamic>{
      if (columnId != null) 'column_id': columnId,
      if (boardPosition != null) 'board_position': boardPosition,
      if (isInBacklog != null) 'is_in_backlog': isInBacklog,
    };
    final res = await _client.dio.post(ApiConfig.taskMove(taskId), data: body);
    return Task.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Task> update(String taskId, Map<String, dynamic> patch) async {
    final res = await _client.dio.patch(
      ApiConfig.taskDetail(taskId),
      data: patch,
    );
    return Task.fromJson(res.data as Map<String, dynamic>);
  }
}
