import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/calendar_event.dart';

class CalendarService {
  CalendarService(this._client);

  final ApiClient _client;

  Future<List<CalendarEvent>> events({
    required String start,
    required String end,
  }) async {
    final res = await _client.dio.get(
      ApiConfig.calendarEvents,
      queryParameters: {'start': start, 'end': end},
    );
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(CalendarEvent.fromJson)
        .toList();
  }

  Future<List<CalendarEvent>> timeline() async {
    final res = await _client.dio.get(ApiConfig.calendarTimeline);
    return ApiClient.unwrapList(res.data)
        .whereType<Map<String, dynamic>>()
        .map(CalendarEvent.fromJson)
        .toList();
  }

  Future<CalendarEvent> create({
    required String title,
    required String startAt,
    required String endAt,
    bool allDay = false,
    String? color,
    String? projectId,
    String? assigneeId,
    String? department,
  }) async {
    final body = <String, dynamic>{
      'title': title,
      'start_at': startAt,
      'end_at': endAt,
      'all_day': allDay,
      if (color != null) 'color': color,
      if (projectId != null) 'project_id': projectId,
      if (assigneeId != null) 'assignee_id': assigneeId,
      if (department != null) 'department': department,
    };
    final res = await _client.dio.post(ApiConfig.calendarEvents, data: body);
    return CalendarEvent.fromJson(res.data as Map<String, dynamic>);
  }
}
