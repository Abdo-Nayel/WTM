import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/task.dart';
import '../services/auth_service.dart';
import '../services/project_service.dart';
import '../services/task_service.dart';
import 'auth_provider.dart';
import 'project_provider.dart';

final taskServiceProvider = Provider<TaskService>((ref) {
  return TaskService(ref.watch(apiClientProvider));
});

class BoardState {
  const BoardState({
    this.data,
    this.isLoading = false,
    this.error,
    this.isMoving = false,
  });

  final BoardData? data;
  final bool isLoading;
  final String? error;
  final bool isMoving;

  BoardState copyWith({
    BoardData? data,
    bool? isLoading,
    String? error,
    bool? isMoving,
    bool clearError = false,
    bool clearData = false,
  }) {
    return BoardState(
      data: clearData ? null : (data ?? this.data),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      isMoving: isMoving ?? this.isMoving,
    );
  }
}

class BoardNotifier extends StateNotifier<BoardState> {
  BoardNotifier(this._ref) : super(const BoardState()) {
    _ref.listen(projectProvider, (prev, next) {
      if (next.selectedId != prev?.selectedId && next.selectedId != null) {
        load(next.selectedId!);
      }
    });
    final id = _ref.read(projectProvider).selectedId;
    if (id != null) load(id);
  }

  final Ref _ref;

  ProjectService get _projects => _ref.read(projectServiceProvider);
  TaskService get _tasks => _ref.read(taskServiceProvider);

  Future<void> load([String? projectId]) async {
    final id = projectId ?? _ref.read(projectProvider).selectedId;
    if (id == null) {
      state = const BoardState();
      return;
    }
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final data = await _projects.board(id);
      state = BoardState(data: data, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _msg(e));
    }
  }

  Future<bool> moveTask({
    required String taskId,
    required String columnId,
    int? boardPosition,
  }) async {
    final current = state.data;
    if (current == null) return false;

    // Optimistic update
    final updatedTasks = current.tasks.map((t) {
      if (t.id == taskId) {
        return t.copyWith(
          columnId: columnId,
          boardPosition: boardPosition ?? t.boardPosition,
          isInBacklog: false,
        );
      }
      return t;
    }).toList();
    state = state.copyWith(
      data: BoardData(
        project: current.project,
        columns: current.columns,
        tasks: updatedTasks,
      ),
      isMoving: true,
      clearError: true,
    );

    try {
      await _tasks.move(
        taskId,
        columnId: columnId,
        boardPosition: boardPosition,
        isInBacklog: false,
      );
      state = state.copyWith(isMoving: false);
      return true;
    } catch (e) {
      await load();
      state = state.copyWith(isMoving: false, error: _msg(e));
      return false;
    }
  }

  Future<Task?> createTask({
    required String projectId,
    required String title,
    String? description,
    String? taskType,
    String? priority,
    int? storyPoints,
    String? dueDate,
    String? columnId,
  }) async {
    try {
      final task = await _tasks.create(
        projectId: projectId,
        title: title,
        description: description,
        taskType: taskType,
        priority: priority,
        storyPoints: storyPoints,
        dueDate: dueDate,
        columnId: columnId,
      );
      await load(projectId);
      return task;
    } catch (e) {
      state = state.copyWith(error: _msg(e));
      return null;
    }
  }

  Future<Task?> updateTask(String taskId, Map<String, dynamic> patch) async {
    try {
      final task = await _tasks.update(taskId, patch);
      await load();
      return task;
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

final boardProvider = StateNotifierProvider<BoardNotifier, BoardState>((ref) {
  return BoardNotifier(ref);
});

class BacklogNotifier extends StateNotifier<AsyncValue<List<Task>>> {
  BacklogNotifier(this._ref) : super(const AsyncValue.loading()) {
    load();
  }

  final Ref _ref;

  TaskService get _tasks => _ref.read(taskServiceProvider);

  Future<void> load() async {
    state = const AsyncValue.loading();
    try {
      final list = await _tasks.backlog();
      state = AsyncValue.data(list);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<bool> moveToBoard(String taskId, String columnId) async {
    try {
      await _tasks.move(taskId, columnId: columnId, isInBacklog: false);
      await load();
      return true;
    } catch (_) {
      return false;
    }
  }
}

final backlogProvider =
    StateNotifierProvider<BacklogNotifier, AsyncValue<List<Task>>>((ref) {
  ref.watch(projectProvider.select((s) => s.selectedId));
  return BacklogNotifier(ref);
});
