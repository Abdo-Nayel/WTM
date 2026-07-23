import 'package:dio/dio.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/user.dart';

class AuthResult {
  const AuthResult({
    required this.access,
    required this.refresh,
    required this.user,
  });

  final String access;
  final String refresh;
  final User user;
}

class AuthService {
  AuthService(this._client);

  final ApiClient _client;

  Dio get _dio => _client.dio;

  Future<AuthResult> login({
    required String email,
    required String password,
  }) async {
    final res = await _dio.post(
      ApiConfig.authToken,
      data: {'email': email, 'password': password},
    );
    return _parseAuth(res.data as Map<String, dynamic>);
  }

  Future<AuthResult> register({
    required String email,
    required String password,
    required String passwordConfirm,
    required String firstName,
    required String lastName,
  }) async {
    await _dio.post(
      ApiConfig.authRegister,
      data: {
        'email': email,
        'password': password,
        'password_confirm': passwordConfirm,
        'first_name': firstName,
        'last_name': lastName,
      },
    );
    return login(email: email, password: password);
  }

  Future<User> me() async {
    final res = await _dio.get(ApiConfig.authMe);
    return User.fromJson(res.data as Map<String, dynamic>);
  }

  /// Request a password-reset email (always succeeds from the client POV).
  Future<void> requestPasswordReset({required String email}) async {
    await _dio.post(
      ApiConfig.authPasswordReset,
      data: {'email': email.trim().toLowerCase()},
    );
  }

  Future<void> confirmPasswordReset({
    required String token,
    required String newPassword,
    required String newPasswordConfirm,
  }) async {
    await _dio.post(
      ApiConfig.authPasswordResetConfirm,
      data: {
        'token': token,
        'new_password': newPassword,
        'new_password_confirm': newPasswordConfirm,
      },
    );
  }

  AuthResult _parseAuth(Map<String, dynamic> data) {
    final userJson = data['user'];
    final user = userJson is Map<String, dynamic>
        ? User.fromJson(userJson)
        : User(id: '', email: data['email'] as String? ?? '');

    return AuthResult(
      access: data['access'] as String? ?? '',
      refresh: data['refresh'] as String? ?? '',
      user: user,
    );
  }

  static String messageFromDio(DioException e) {
    final data = e.response?.data;
    if (data is Map) {
      if (data['detail'] != null) return data['detail'].toString();
      if (data['error'] != null) return data['error'].toString();
      final parts = <String>[];
      data.forEach((key, value) {
        if (value is List) {
          parts.add('$key: ${value.join(', ')}');
        } else if (value is String) {
          parts.add('$key: $value');
        }
      });
      if (parts.isNotEmpty) return parts.join('\n');
    }
    return e.message ?? 'Network error';
  }
}
