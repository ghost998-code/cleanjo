part of 'auth_bloc.dart';

abstract class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object?> get props => [];
}

class CheckAuthStatus extends AuthEvent {}

class RequestOtpRequested extends AuthEvent {
  final String phone;

  const RequestOtpRequested({required this.phone});

  @override
  List<Object?> get props => [phone];
}

class VerifyOtpRequested extends AuthEvent {
  final String phone;
  final String otp;

  const VerifyOtpRequested({required this.phone, required this.otp});

  @override
  List<Object?> get props => [phone, otp];
}

class LogoutRequested extends AuthEvent {}
