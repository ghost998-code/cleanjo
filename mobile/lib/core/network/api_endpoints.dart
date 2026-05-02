import 'dart:io';

class ApiEndpoints {
  static const String _configuredBaseUrl = String.fromEnvironment('CLEANJO_API_BASE_URL');

  static String get baseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      return _configuredBaseUrl;
    }

    final host = Platform.isAndroid ? '10.0.2.2' : 'localhost';
    return 'http://$host:8000/api/v1';
  }

  static const String requestPhoneOtp = '/auth/request-phone-otp';
  static const String verifyPhoneOtp = '/auth/verify-phone-otp';
  static const String refresh = '/auth/refresh';
  static const String me = '/auth/me';
  static const String mobileConfig = '/config/mobile';

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
