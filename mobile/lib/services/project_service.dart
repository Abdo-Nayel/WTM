import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/project.dart';
import '../models/task.dart';

class ProjectService {
  ProjectService(this._client);

  final ApiClient _client;

  Future<List<Project>> list() async {
    final res = await _client.dio.get(ApiConfig.projects);
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(Project.fromJson)
        .toList();
  }

  Future<Project> create({
    required String name,
    required String key,
    String? description,
    String? color,
  }) async {
    final body = <String, dynamic>{
      'name': name,
      'key': key,
      if (description != null && description.isNotEmpty)
        'description': description,
      if (color != null && color.isNotEmpty) 'color': color,
    };
    final res = await _client.dio.post(ApiConfig.projects, data: body);
    return Project.fromJson(res.data as Map<String, dynamic>);
  }

  Future<BoardData> board(String projectId) async {
    final res = await _client.dio.get(ApiConfig.projectBoard(projectId));
    return BoardData.fromJson(res.data as Map<String, dynamic>);
  }
}
