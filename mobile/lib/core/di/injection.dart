import 'package:get_it/get_it.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:dio/dio.dart';

import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import '../auth/auth_bloc.dart';
import '../auth/auth_repository.dart';
import '../config/mobile_config_service.dart';
import '../inference/on_device_inference_service.dart';
import '../offline/sync_service.dart';

final getIt = GetIt.instance;

Future<void> initDependencies() async {
  await Hive.initFlutter();
  await Hive.openBox('pending_reports');
  final configBox = await Hive.openBox<String>('app_config');

  getIt.registerLazySingleton(() => const FlutterSecureStorage());
  getIt.registerLazySingleton(() => Dio(BaseOptions(
        baseUrl: ApiEndpoints.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
      )));

  getIt.registerLazySingleton(
      () => ApiClient(getIt<Dio>(), getIt<FlutterSecureStorage>()));
  getIt.registerLazySingleton(() => AuthRepository(getIt<ApiClient>()));
  getIt.registerLazySingleton(
      () => MobileConfigService(getIt<ApiClient>(), configBox));
  getIt.registerLazySingleton(() => OnDeviceInferenceService());
  getIt.registerLazySingleton(() => SyncService(getIt<ApiClient>()));

  getIt.registerFactory(() => AuthBloc(
        authRepository: getIt<AuthRepository>(),
        secureStorage: getIt<FlutterSecureStorage>(),
      ));
}
