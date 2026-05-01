import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import 'auth_models.dart';

class AuthRepository {
  final ApiClient _apiClient;

  AuthRepository(this._apiClient);

  Future<Map<String, dynamic>> requestOtp(String phone) async {
    final response = await _apiClient.post(
      ApiEndpoints.requestPhoneOtp,
      data: {'phone': phone},
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> loginWithOtp(String phone, String otp) async {
    final response = await _apiClient.post(
      ApiEndpoints.verifyPhoneOtp,
      data: {'phone': phone, 'otp': otp},
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<UserModel> getCurrentUser() async {
    final response = await _apiClient.get(ApiEndpoints.me);
    return UserModel.fromJson(response.data);
  }
}
