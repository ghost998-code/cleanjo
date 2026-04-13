import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../auth_repository.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/di/injection.dart';
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
    on<LoginRequested>(_onLoginRequested);
    on<RegisterRequested>(_onRegisterRequested);
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
        emit(AuthAuthenticated(user: response));
      } catch (_) {
        await _clearAuth();
        emit(AuthUnauthenticated());
      }
    } else {
      emit(AuthUnauthenticated());
    }
  }

  Future<void> _onLoginRequested(
    LoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final response = await authRepository.login(event.email, event.password);
      await secureStorage.write(key: 'access_token', value: response['access_token']);
      await secureStorage.write(key: 'refresh_token', value: response['refresh_token']);
      
      final userResponse = await authRepository.getCurrentUser();
      emit(AuthAuthenticated(user: userResponse));
    } catch (e) {
      emit(AuthError(message: _parseError(e)));
    }
  }

  Future<void> _onRegisterRequested(
    RegisterRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      await authRepository.register(
        email: event.email,
        password: event.password,
        fullName: event.fullName,
        role: event.role,
      );
      emit(AuthRegistrationSuccess());
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
    if (e.toString().contains('401')) {
      return 'Invalid email or password';
    }
    if (e.toString().contains('400')) {
      return 'Email already registered';
    }
    return 'An error occurred. Please try again.';
  }
}
