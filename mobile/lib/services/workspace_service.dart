import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/workspace.dart';

class WorkspaceService {
  WorkspaceService(this._client);

  final ApiClient _client;

  Future<List<Workspace>> list() async {
    final res = await _client.dio.get(ApiConfig.workspaces);
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(Workspace.fromJson)
        .toList();
  }

  Future<Workspace> create({
    required String name,
    String? description,
    String? defaultKeyPrefix,
  }) async {
    final body = <String, dynamic>{
      'name': name,
      if (description != null && description.isNotEmpty)
        'description': description,
      if (defaultKeyPrefix != null && defaultKeyPrefix.isNotEmpty)
        'default_key_prefix': defaultKeyPrefix,
    };
    final res = await _client.dio.post(ApiConfig.workspaces, data: body);
    return Workspace.fromJson(res.data as Map<String, dynamic>);
  }
}
