class ApiConfig {
  ApiConfig._();

  /// Django backend. On Android emulator use `http://10.0.2.2:8000`.
  static const String baseUrl = 'http://127.0.0.1:8000';

  static const String authRegister = '/api/auth/register/';
  static const String authToken = '/api/auth/token/';
  static const String authRefresh = '/api/auth/token/refresh/';
  static const String authMe = '/api/auth/me/';

  static const String workspaces = '/api/workspaces/';
  static const String projects = '/api/projects/';
  static const String tasks = '/api/tasks/';
  static const String tasksBacklog = '/api/tasks/backlog/';
  static const String calendarEvents = '/api/calendar/events/';
  static const String calendarTimeline = '/api/calendar/events/timeline/';

  static String projectBoard(String id) => '/api/projects/$id/board/';
  static String taskDetail(String id) => '/api/tasks/$id/';
  static String taskMove(String id) => '/api/tasks/$id/move/';
}
