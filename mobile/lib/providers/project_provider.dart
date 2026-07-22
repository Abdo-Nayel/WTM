import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/project.dart';
import '../services/auth_service.dart';
import '../services/project_service.dart';
import 'auth_provider.dart';
import 'workspace_provider.dart';

final projectServiceProvider = Provider<ProjectService>((ref) {
  return ProjectService(ref.watch(apiClientProvider));
});

class ProjectState {
  const ProjectState({
    this.projects = const [],
    this.selectedId,
    this.isLoading = false,
    this.error,
  });

  final List<Project> projects;
  final String? selectedId;
  final bool isLoading;
  final String? error;

  Project? get selected {
    if (selectedId == null) return null;
    for (final p in projects) {
      if (p.id == selectedId) return p;
    }
    return null;
  }

  ProjectState copyWith({
    List<Project>? projects,
    String? selectedId,
    bool? isLoading,
    String? error,
    bool clearSelected = false,
    bool clearError = false,
  }) {
    return ProjectState(
      projects: projects ?? this.projects,
      selectedId: clearSelected ? null : (selectedId ?? this.selectedId),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class ProjectNotifier extends StateNotifier<ProjectState> {
  ProjectNotifier(this._ref) : super(const ProjectState()) {
    _ref.listen(workspaceProvider, (prev, next) {
      if (next.current?.id != prev?.current?.id) {
        if (next.current != null) {
          load();
        } else {
          state = const ProjectState();
        }
      }
    });
    if (_ref.read(workspaceProvider).current != null) {
      load();
    }
  }

  final Ref _ref;

  ProjectService get _service => _ref.read(projectServiceProvider);

  Future<void> load() async {
    if (_ref.read(workspaceProvider).current == null) return;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final list = await _service.list();
      String? selected = state.selectedId;
      if (selected != null && !list.any((p) => p.id == selected)) {
        selected = null;
      }
      selected ??= list.isNotEmpty ? list.first.id : null;
      state = ProjectState(
        projects: list,
        selectedId: selected,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _msg(e));
    }
  }

  void select(String projectId) {
    state = state.copyWith(selectedId: projectId);
  }

  Future<Project?> create({
    required String name,
    required String key,
    String? description,
    String? color,
  }) async {
    try {
      final p = await _service.create(
        name: name,
        key: key,
        description: description,
        color: color,
      );
      final list = [...state.projects, p];
      state = state.copyWith(
        projects: list,
        selectedId: p.id,
        clearError: true,
      );
      return p;
    } catch (e) {
      state = state.copyWith(error: _msg(e));
      return null;
    }
  }

  String _msg(Object e) {
    if (e is DioException) return AuthService.messageFromDio(e);
    return e.toString();
  }
}

final projectProvider =
    StateNotifierProvider<ProjectNotifier, ProjectState>((ref) {
  return ProjectNotifier(ref);
});
