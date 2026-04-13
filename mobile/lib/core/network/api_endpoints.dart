class ApiEndpoints {
  static const String baseUrl = 'http://localhost:8000/api';
  
  static const String login = '/auth/login';
  static const String register = '/auth/register';
  static const String refresh = '/auth/refresh';
  static const String me = '/auth/me';
  
  static const String reports = '/reports';
  static String report(String id) => '/reports/$id';
  static const String reportsMap = '/reports/map';
  static String reportHistory(String id) => '/reports/$id/history';
  
  static const String users = '/users';
  static String user(String id) => '/users/$id';
  static String updateRole(String id) => '/users/$id/role';
  
  static const String analyticsSummary = '/analytics/summary';
  static const String analyticsHeatmap = '/analytics/heatmap';
}
