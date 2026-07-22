import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/storage/token_storage.dart';
import '../models/workspace.dart';
import '../services/auth_service.dart';
import '../services/workspace_service.dart';
import 'auth_provider.dart';

final workspaceServiceProvider = Provider<WorkspaceService>((ref) {
  return WorkspaceService(ref.watch(apiClientProvider));
});

class WorkspaceState {
  const WorkspaceState({
    this.workspaces = const [],
    this.current,
    this.isLoading = false,
    this.error,
  });

  final List<Workspace> workspaces;
  final Workspace? current;
  final bool isLoading;
  final String? error;

  WorkspaceState copyWith({
    List<Workspace>? workspaces,
    Workspace? current,
    bool? isLoading,
    String? error,
    bool clearCurrent = false,
    bool clearError = false,
  }) {
    return WorkspaceState(
      workspaces: workspaces ?? this.workspaces,
      current: clearCurrent ? null : (current ?? this.current),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class WorkspaceNotifier extends StateNotifier<WorkspaceState> {
  WorkspaceNotifier(this._ref) : super(const WorkspaceState()) {
    _ref.listen<AuthState>(authProvider, (prev, next) {
      if (next.status == AuthStatus.authenticated &&
          prev?.status != AuthStatus.authenticated) {
        load();
      }
      if (next.status == AuthStatus.unauthenticated) {
        state = const WorkspaceState();
      }
    });
    if (_ref.read(authProvider).status == AuthStatus.authenticated) {
      load();
    }
  }

  final Ref _ref;

  TokenStorage get _storage => _ref.read(tokenStorageProvider);
  WorkspaceService get _service => _ref.read(workspaceServiceProvider);

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final list = await _service.list();
      Workspace? current;
      final savedId = _storage.workspaceId;
      if (savedId != null) {
        for (final w in list) {
          if (w.id == savedId) {
            current = w;
            break;
          }
        }
      }
      state = WorkspaceState(
        workspaces: list,
        current: current,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: _msg(e),
      );
    }
  }

  Future<void> select(Workspace workspace) async {
    await _storage.saveWorkspaceId(workspace.id);
    state = state.copyWith(current: workspace);
  }

  Future<Workspace?> create({
    required String name,
    String? description,
    String? defaultKeyPrefix,
  }) async {
    try {
      final ws = await _service.create(
        name: name,
        description: description,
        defaultKeyPrefix: defaultKeyPrefix,
      );
      final updated = [...state.workspaces, ws];
      await _storage.saveWorkspaceId(ws.id);
      state = state.copyWith(workspaces: updated, current: ws, clearError: true);
      return ws;
    } catch (e) {
      state = state.copyWith(error: _msg(e));
      return null;
    }
  }

  Future<void> clearSelection() async {
    await _storage.saveWorkspaceId(null);
    state = state.copyWith(clearCurrent: true);
  }

  String _msg(Object e) {
    if (e is DioException) return AuthService.messageFromDio(e);
    return e.toString();
  }
}

final workspaceProvider =
    StateNotifierProvider<WorkspaceNotifier, WorkspaceState>((ref) {
  return WorkspaceNotifier(ref);
});
