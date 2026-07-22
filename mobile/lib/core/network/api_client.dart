import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../storage/token_storage.dart';
import 'auth_interceptor.dart';

class ApiClient {
  ApiClient({
    required TokenStorage tokenStorage,
    void Function()? onUnauthorized,
  }) : _tokenStorage = tokenStorage {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      AuthInterceptor(
        dio: _dio,
        tokenStorage: _tokenStorage,
        onUnauthorized: onUnauthorized,
      ),
    );
  }

  final TokenStorage _tokenStorage;
  late final Dio _dio;

  Dio get dio => _dio;

  /// Parses DRF paginated `{results: [...]}` or a plain list.
  static List<dynamic> unwrapList(dynamic data) {
    if (data == null) return const [];
    if (data is List) return data;
    if (data is Map && data['results'] is List) {
      return data['results'] as List;
    }
    return const [];
  }
}
