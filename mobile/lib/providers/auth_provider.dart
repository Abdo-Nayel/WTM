import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/api_client.dart';
import '../core/storage/token_storage.dart';
import '../models/user.dart';
import '../services/auth_service.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) {
  throw UnimplementedError('tokenStorageProvider must be overridden in main()');
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(tokenStorageProvider);
  return ApiClient(
    tokenStorage: storage,
    onUnauthorized: () {
      ref.read(authProvider.notifier).forceLogout();
    },
  );
});

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref.watch(apiClientProvider));
});

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState {
  const AuthState({
    this.status = AuthStatus.unknown,
    this.user,
    this.error,
    this.isLoading = false,
  });

  final AuthStatus status;
  final User? user;
  final String? error;
  final bool isLoading;

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? error,
    bool? isLoading,
    bool clearUser = false,
    bool clearError = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: clearUser ? null : (user ?? this.user),
      error: clearError ? null : (error ?? this.error),
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._ref) : super(const AuthState()) {
    _bootstrap();
  }

  final Ref _ref;

  TokenStorage get _storage => _ref.read(tokenStorageProvider);
  AuthService get _service => _ref.read(authServiceProvider);

  Future<void> _bootstrap() async {
    if (!_storage.hasTokens) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    try {
      final user = await _service.me();
      state = AuthState(status: AuthStatus.authenticated, user: user);
    } catch (_) {
      await _storage.clear();
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<bool> login({required String email, required String password}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final result = await _service.login(email: email, password: password);
      await applyAuthResult(result);
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _errorMessage(e),
        status: AuthStatus.unauthenticated,
      );
      return false;
    }
  }

  Future<void> applyAuthResult(AuthResult result) async {
    await _storage.saveTokens(access: result.access, refresh: result.refresh);
    state = AuthState(
      status: AuthStatus.authenticated,
      user: result.user,
      isLoading: false,
    );
  }

  Future<bool> register({
    required String email,
    required String password,
    required String passwordConfirm,
    required String firstName,
    required String lastName,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final result = await _service.register(
        email: email,
        password: password,
        passwordConfirm: passwordConfirm,
        firstName: firstName,
        lastName: lastName,
      );
      await _storage.saveTokens(access: result.access, refresh: result.refresh);
      state = AuthState(
        status: AuthStatus.authenticated,
        user: result.user,
        isLoading: false,
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _errorMessage(e),
        status: AuthStatus.unauthenticated,
      );
      return false;
    }
  }

  Future<void> logout() async {
    await _storage.clear();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void forceLogout() {
    Future.microtask(() async {
      await _storage.clear();
      state = const AuthState(status: AuthStatus.unauthenticated);
    });
  }

  String _errorMessage(Object e) {
    if (e is DioException) return AuthService.messageFromDio(e);
    return e.toString();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});
