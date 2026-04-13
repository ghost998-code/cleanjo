import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'core/di/injection.dart';
import 'core/network/api_client.dart';
import 'core/auth/auth_bloc.dart';
import 'features/home/pages/home_page.dart';
import 'features/auth/pages/login_page.dart';
import 'features/auth/pages/register_page.dart';
import 'features/citizen/pages/create_report_page.dart';
import 'features/inspector/pages/inspector_dashboard_page.dart';
import 'features/map/pages/map_page.dart';
import 'features/profile/pages/profile_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initDependencies();
  runApp(const GarbageDetectionApp());
}

class GarbageDetectionApp extends StatelessWidget {
  const GarbageDetectionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<AuthBloc>()..add(CheckAuthStatus()),
      child: MaterialApp(
        title: 'Garbage Detection',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
          useMaterial3: true,
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => const AuthWrapper(),
          '/login': (context) => const LoginPage(),
          '/register': (context) => const RegisterPage(),
          '/home': (context) => const HomePage(),
          '/create-report': (context) => const CreateReportPage(),
          '/map': (context) => const MapPage(),
          '/inspector': (context) => const InspectorDashboardPage(),
          '/profile': (context) => const ProfilePage(),
        },
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        if (state is AuthAuthenticated) {
          return const HomePage();
        }
        return const LoginPage();
      },
    );
  }
}
