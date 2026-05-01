import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'package:garbage_detection_app/core/auth/auth_bloc.dart';
import 'package:garbage_detection_app/core/auth/auth_repository.dart';
import 'package:garbage_detection_app/core/network/api_client.dart';
import 'package:garbage_detection_app/features/auth/pages/login_page.dart';

void main() {
  testWidgets('otp login screen builds', (WidgetTester tester) async {
    const secureStorage = FlutterSecureStorage();
    final authBloc = AuthBloc(
      authRepository: AuthRepository(ApiClient(Dio(), secureStorage)),
      secureStorage: secureStorage,
    );

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider.value(
          value: authBloc,
          child: const LoginPage(),
        ),
      ),
    );

    expect(find.text('Garbage Detection'), findsOneWidget);
    expect(find.text('Register or sign in with your phone number and OTP'), findsOneWidget);
    expect(find.text('Phone Number'), findsOneWidget);
  });
}
