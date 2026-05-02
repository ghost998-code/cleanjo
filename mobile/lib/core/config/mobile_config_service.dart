import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import 'mobile_runtime_config.dart';

class MobileConfigService {
  static const _configKey = 'mobile_runtime_config';

  final ApiClient _apiClient;
  final Box<String> _configBox;

  MobileRuntimeConfig _currentConfig = MobileRuntimeConfig.fallback;

  MobileConfigService(this._apiClient, this._configBox);

  MobileRuntimeConfig get currentConfig => _currentConfig;

  Future<void> initialize() async {
    _currentConfig = await getCachedOrFallback();

    try {
      await refresh();
    } catch (_) {
      // Keep cached or fallback values for offline use.
    }
  }

  Future<MobileRuntimeConfig> refresh() async {
    final response = await _apiClient.get(ApiEndpoints.mobileConfig);
    final config = MobileRuntimeConfig.fromJson(
      Map<String, dynamic>.from(response.data as Map),
    );
    await _configBox.put(_configKey, jsonEncode(config.toJson()));
    _currentConfig = config;
    return config;
  }

  Future<MobileRuntimeConfig> getCachedOrFallback() async {
    final cached = _configBox.get(_configKey);
    if (cached == null || cached.isEmpty) {
      return MobileRuntimeConfig.fallback;
    }

    try {
      return MobileRuntimeConfig.fromJson(
        Map<String, dynamic>.from(jsonDecode(cached) as Map),
      );
    } catch (_) {
      return MobileRuntimeConfig.fallback;
    }
  }
}
