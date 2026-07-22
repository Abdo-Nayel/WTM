import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  TokenStorage(this._prefs);

  final SharedPreferences _prefs;

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _workspaceKey = 'workspace_id';

  Future<void> saveTokens({required String access, required String refresh}) async {
    await _prefs.setString(_accessKey, access);
    await _prefs.setString(_refreshKey, refresh);
  }

  Future<void> saveAccessToken(String access) async {
    await _prefs.setString(_accessKey, access);
  }

  String? get accessToken => _prefs.getString(_accessKey);
  String? get refreshToken => _prefs.getString(_refreshKey);
  String? get workspaceId => _prefs.getString(_workspaceKey);

  Future<void> saveWorkspaceId(String? id) async {
    if (id == null || id.isEmpty) {
      await _prefs.remove(_workspaceKey);
    } else {
      await _prefs.setString(_workspaceKey, id);
    }
  }

  Future<void> clear() async {
    await _prefs.remove(_accessKey);
    await _prefs.remove(_refreshKey);
    await _prefs.remove(_workspaceKey);
  }

  bool get hasTokens =>
      accessToken != null &&
      accessToken!.isNotEmpty &&
      refreshToken != null &&
      refreshToken!.isNotEmpty;
}
