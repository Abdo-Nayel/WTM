import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../storage/token_storage.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required this.dio,
    required this.tokenStorage,
    this.onUnauthorized,
  });

  final Dio dio;
  final TokenStorage tokenStorage;
  final void Function()? onUnauthorized;

  bool _isRefreshing = false;
  final List<_RetryEntry> _queue = [];

  bool _isAuthPath(String path) {
    return path.contains('/api/auth/');
  }

  bool _isWorkspaceListOrCreate(RequestOptions options) {
    final path = options.path;
    final normalized = path.endsWith('/') ? path : '$path/';
    final isRoot = normalized.endsWith('/api/workspaces/') ||
        normalized == ApiConfig.workspaces ||
        normalized == '${ApiConfig.workspaces}/';
    if (!isRoot && !path.contains('/api/workspaces')) return false;
    // Only list (GET collection) and create (POST collection) skip workspace header.
    if (!isRoot) return false;
    final method = options.method.toUpperCase();
    return method == 'GET' || method == 'POST';
  }

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (!_isAuthPath(options.path)) {
      final access = tokenStorage.accessToken;
      if (access != null && access.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $access';
      }

      if (!_isWorkspaceListOrCreate(options)) {
        final ws = tokenStorage.workspaceId;
        if (ws != null && ws.isNotEmpty) {
          options.headers['X-Workspace-Id'] = ws;
        }
      }
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final path = err.requestOptions.path;

    if (status != 401 || path.contains(ApiConfig.authRefresh)) {
      handler.next(err);
      return;
    }

    // Don't try refresh on login/register failures.
    if (path.contains(ApiConfig.authToken) ||
        path.contains(ApiConfig.authRegister)) {
      handler.next(err);
      return;
    }

    final refresh = tokenStorage.refreshToken;
    if (refresh == null || refresh.isEmpty) {
      onUnauthorized?.call();
      handler.next(err);
      return;
    }

    if (_isRefreshing) {
      _queue.add(_RetryEntry(err.requestOptions, handler));
      return;
    }

    _isRefreshing = true;
    try {
      final refreshDio = Dio(
        BaseOptions(
          baseUrl: ApiConfig.baseUrl,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        ),
      );
      final res = await refreshDio.post(
        ApiConfig.authRefresh,
        data: {'refresh': refresh},
      );
      final newAccess = res.data['access'] as String?;
      if (newAccess == null || newAccess.isEmpty) {
        throw DioException(
          requestOptions: err.requestOptions,
          error: 'No access token',
        );
      }
      await tokenStorage.saveAccessToken(newAccess);

      final opts = err.requestOptions;
      opts.headers['Authorization'] = 'Bearer $newAccess';
      final response = await dio.fetch(opts);
      handler.resolve(response);

      for (final entry in List<_RetryEntry>.from(_queue)) {
        entry.options.headers['Authorization'] = 'Bearer $newAccess';
        try {
          final r = await dio.fetch(entry.options);
          entry.handler.resolve(r);
        } catch (e) {
          if (e is DioException) {
            entry.handler.next(e);
          } else {
            entry.handler.next(
              DioException(requestOptions: entry.options, error: e),
            );
          }
        }
      }
      _queue.clear();
    } catch (_) {
      _queue.clear();
      await tokenStorage.clear();
      onUnauthorized?.call();
      handler.next(err);
    } finally {
      _isRefreshing = false;
    }
  }
}

class _RetryEntry {
  _RetryEntry(this.options, this.handler);
  final RequestOptions options;
  final ErrorInterceptorHandler handler;
}
