import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'auth_repository.dart';
import 'auth_models.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

part 'auth_event.dart';
part 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository authRepository;
  final FlutterSecureStorage secureStorage;

  AuthBloc({
    required this.authRepository,
    required this.secureStorage,
  }) : super(AuthInitial()) {
    on<CheckAuthStatus>(_onCheckAuthStatus);
    on<RequestOtpRequested>(_onRequestOtpRequested);
    on<VerifyOtpRequested>(_onVerifyOtpRequested);
    on<LogoutRequested>(_onLogoutRequested);
  }

  Future<void> _onCheckAuthStatus(
    CheckAuthStatus event,
    Emitter<AuthState> emit,
  ) async {
    final token = await secureStorage.read(key: 'access_token');
    final userData = await secureStorage.read(key: 'user_data');
    
    if (token != null && userData != null) {
      try {
        final response = await authRepository.getCurrentUser();
        await secureStorage.write(
          key: 'user_data',
          value: jsonEncode(response.toJson()),
        );
        emit(AuthAuthenticated(user: response));
      } catch (_) {
        await _clearAuth();
        emit(AuthUnauthenticated());
      }
    } else {
      emit(AuthUnauthenticated());
    }
  }

  Future<void> _onRequestOtpRequested(
    RequestOtpRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final response = await authRepository.requestOtp(event.phone);
      emit(
        AuthOtpRequested(
          phone: event.phone,
          message: (response['message'] as String?) ?? 'OTP sent successfully',
          devOtp: response['otp'] as String?,
        ),
      );
    } catch (e) {
      emit(AuthError(message: _parseError(e)));
    }
  }

  Future<void> _onVerifyOtpRequested(
    VerifyOtpRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final response = await authRepository.loginWithOtp(event.phone, event.otp);
      await secureStorage.write(key: 'access_token', value: response['access_token']);
      await secureStorage.write(key: 'refresh_token', value: response['refresh_token']);

      final userResponse = await authRepository.getCurrentUser();
      await secureStorage.write(
        key: 'user_data',
        value: jsonEncode(userResponse.toJson()),
      );
      emit(AuthAuthenticated(user: userResponse));
    } catch (e) {
      emit(AuthError(message: _parseError(e)));
    }
  }

  Future<void> _onLogoutRequested(
    LogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await _clearAuth();
    emit(AuthUnauthenticated());
  }

  Future<void> _clearAuth() async {
    await secureStorage.delete(key: 'access_token');
    await secureStorage.delete(key: 'refresh_token');
    await secureStorage.delete(key: 'user_data');
  }

  String _parseError(dynamic e) {
    if (e is DioException) {
      final detail = e.response?.data is Map<String, dynamic>
          ? (e.response?.data['detail'] as String?)
          : null;
      if (detail != null && detail.isNotEmpty) {
        return detail;
      }

      if (e.response?.statusCode == 401) {
        return 'Invalid credentials';
      }

      if (e.response?.statusCode == 400) {
        return 'The request could not be completed';
      }
    }

    if (e.toString().contains('401')) {
      return 'Invalid credentials';
    }

    if (e.toString().contains('400')) {
      return 'The request could not be completed';
    }

    return 'An error occurred. Please try again.';
  }
}
