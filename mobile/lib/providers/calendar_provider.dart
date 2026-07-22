import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../models/calendar_event.dart';
import '../services/auth_service.dart';
import '../services/calendar_service.dart';
import 'auth_provider.dart';
import 'workspace_provider.dart';

final calendarServiceProvider = Provider<CalendarService>((ref) {
  return CalendarService(ref.watch(apiClientProvider));
});

class CalendarState {
  const CalendarState({
    this.events = const [],
    this.isLoading = false,
    this.error,
    this.focusedDay,
    this.selectedDay,
    this.isWeekView = false,
  });

  final List<CalendarEvent> events;
  final bool isLoading;
  final String? error;
  final DateTime? focusedDay;
  final DateTime? selectedDay;
  final bool isWeekView;

  CalendarState copyWith({
    List<CalendarEvent>? events,
    bool? isLoading,
    String? error,
    DateTime? focusedDay,
    DateTime? selectedDay,
    bool? isWeekView,
    bool clearError = false,
  }) {
    return CalendarState(
      events: events ?? this.events,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      focusedDay: focusedDay ?? this.focusedDay,
      selectedDay: selectedDay ?? this.selectedDay,
      isWeekView: isWeekView ?? this.isWeekView,
    );
  }

  List<CalendarEvent> eventsForDay(DateTime day) {
    return events.where((e) {
      final s = DateTime(e.startAt.year, e.startAt.month, e.startAt.day);
      final d = DateTime(day.year, day.month, day.day);
      final end = DateTime(e.endAt.year, e.endAt.month, e.endAt.day);
      return !d.isBefore(s) && !d.isAfter(end);
    }).toList();
  }
}

class CalendarNotifier extends StateNotifier<CalendarState> {
  CalendarNotifier(this._ref)
      : super(CalendarState(
          focusedDay: DateTime.now(),
          selectedDay: DateTime.now(),
        )) {
    _ref.listen(workspaceProvider, (prev, next) {
      if (next.current?.id != prev?.current?.id && next.current != null) {
        loadForMonth(state.focusedDay ?? DateTime.now());
      }
    });
    if (_ref.read(workspaceProvider).current != null) {
      loadForMonth(DateTime.now());
    }
  }

  final Ref _ref;
  final _fmt = DateFormat('yyyy-MM-dd');

  CalendarService get _service => _ref.read(calendarServiceProvider);

  Future<void> loadForMonth(DateTime month) async {
    final start = DateTime(month.year, month.month, 1)
        .subtract(const Duration(days: 7));
    final end = DateTime(month.year, month.month + 1, 0)
        .add(const Duration(days: 7));
    await _load(start, end, focused: month);
  }

  Future<void> _load(DateTime start, DateTime end, {DateTime? focused}) async {
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      focusedDay: focused ?? state.focusedDay,
    );
    try {
      final list = await _service.events(
        start: _fmt.format(start),
        end: _fmt.format(end),
      );
      state = state.copyWith(events: list, isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e is DioException ? AuthService.messageFromDio(e) : e.toString(),
      );
    }
  }

  void setFocusedDay(DateTime day) {
    state = state.copyWith(focusedDay: day);
  }

  void setSelectedDay(DateTime day) {
    state = state.copyWith(selectedDay: day, focusedDay: day);
  }

  void toggleView() {
    state = state.copyWith(isWeekView: !state.isWeekView);
  }

  Future<CalendarEvent?> createEvent({
    required String title,
    required DateTime startAt,
    required DateTime endAt,
    bool allDay = false,
    String? color,
    String? projectId,
    String? department,
  }) async {
    try {
      final event = await _service.create(
        title: title,
        startAt: startAt.toIso8601String(),
        endAt: endAt.toIso8601String(),
        allDay: allDay,
        color: color,
        projectId: projectId,
        department: department,
      );
      await loadForMonth(state.focusedDay ?? DateTime.now());
      return event;
    } catch (e) {
      state = state.copyWith(
        error: e is DioException ? AuthService.messageFromDio(e) : e.toString(),
      );
      return null;
    }
  }
}

final calendarProvider =
    StateNotifierProvider<CalendarNotifier, CalendarState>((ref) {
  return CalendarNotifier(ref);
});
