import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/auth/auth_bloc.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  bool _otpRequested = false;
  String? _devOtp;
  String? _otpMessage;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  void _requestOtp() {
    if (_formKey.currentState!.validate()) {
      context.read<AuthBloc>().add(
        RequestOtpRequested(phone: _phoneController.text.trim()),
      );
    }
  }

  void _verifyOtp() {
    if (_formKey.currentState!.validate()) {
      context.read<AuthBloc>().add(
        VerifyOtpRequested(
          phone: _phoneController.text.trim(),
          otp: _otpController.text.trim(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocListener<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message), backgroundColor: Colors.red),
            );
          } else if (state is AuthOtpRequested) {
            setState(() {
              _otpRequested = true;
              _devOtp = state.devOtp;
              _otpMessage = state.devOtp != null
                  ? 'OTP sent. Dev OTP: ${state.devOtp}'
                  : state.message;
            });
          } else if (state is AuthAuthenticated) {
            Navigator.of(context).pushReplacementNamed('/home');
          }
        },
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.delete_sweep,
                      size: 80,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Garbage Detection',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Register or sign in with your phone number and OTP',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 48),
                    if (_otpMessage != null) ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(_otpMessage!),
                      ),
                      const SizedBox(height: 16),
                    ],
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(
                        labelText: 'Phone Number',
                        prefixIcon: Icon(Icons.phone_outlined),
                        border: OutlineInputBorder(),
                        hintText: '+9627...',
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Please enter your phone number';
                        }
                        return null;
                      },
                    ),
                    if (_otpRequested) ...[
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _otpController,
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                          LengthLimitingTextInputFormatter(6),
                        ],
                        decoration: InputDecoration(
                          labelText: 'One-Time Password',
                          prefixIcon: const Icon(Icons.pin_outlined),
                          border: const OutlineInputBorder(),
                          hintText: _devOtp ?? '6-digit code',
                        ),
                        validator: (value) {
                          if (!_otpRequested) return null;
                          if (value == null || value.trim().length != 6) {
                            return 'Enter the 6-digit OTP';
                          }
                          return null;
                        },
                      ),
                    ],
                    const SizedBox(height: 12),
                    Text(
                      _otpRequested
                          ? 'Enter the verification code sent to your phone.'
                          : 'Your first verified OTP will create your account automatically.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 24),
                    BlocBuilder<AuthBloc, AuthState>(
                      builder: (context, state) {
                        final isLoading = state is AuthLoading;
                        return FilledButton(
                          onPressed: isLoading
                              ? null
                              : _otpRequested
                                  ? _verifyOtp
                                  : _requestOtp,
                          child: isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : Text(
                                  _otpRequested ? 'Verify OTP' : 'Send OTP',
                                ),
                        );
                      },
                    ),
                    if (_otpRequested) ...[
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: () {
                          _otpController.clear();
                          _requestOtp();
                        },
                        child: const Text('Resend OTP'),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
