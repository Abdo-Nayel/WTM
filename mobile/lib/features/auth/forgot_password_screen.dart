import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/branding/brand.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../services/auth_service.dart';
import '../../widgets/wtm_logo.dart';

/// Forgot password: email → OTP → new password → signed in.
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _emailCtrl = TextEditingController();
  final _otpCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _pass2Ctrl = TextEditingController();
  int _step = 0; // 0 email, 1 otp, 2 password
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _otpCtrl.dispose();
    _passCtrl.dispose();
    _pass2Ctrl.dispose();
    super.dispose();
  }

  Future<void> _sendCode() async {
    final email = _emailCtrl.text.trim().toLowerCase();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = 'Enter a valid email');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authServiceProvider).requestPasswordReset(email: email);
      if (!mounted) return;
      setState(() {
        _step = 1;
        _otpCtrl.clear();
      });
    } on DioException catch (e) {
      if (!mounted) return;
      final msg = AuthService.messageFromDio(e);
      setState(() {
        _error = RegExp(
          r'not found|no account|Create an account',
          caseSensitive: false,
        ).hasMatch(msg)
            ? 'This email is not registered. Create an account first.'
            : msg;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _continueFromOtp() {
    final code = _otpCtrl.text.trim();
    if (code.length < 4) {
      setState(() => _error = 'Enter the 6-digit code');
      return;
    }
    setState(() {
      _error = null;
      _step = 2;
      _passCtrl.clear();
      _pass2Ctrl.clear();
    });
  }

  Future<void> _savePassword() async {
    final p1 = _passCtrl.text;
    final p2 = _pass2Ctrl.text;
    if (p1.length < 8) {
      setState(() => _error = 'Password must be at least 8 characters');
      return;
    }
    if (p1 != p2) {
      setState(() => _error = 'Passwords do not match');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref.read(authServiceProvider).confirmPasswordReset(
            email: _emailCtrl.text.trim().toLowerCase(),
            code: _otpCtrl.text.trim(),
            newPassword: p1,
            newPasswordConfirm: p2,
          );
      await ref.read(authProvider.notifier).applyAuthResult(result);
      if (!mounted) return;
      context.go('/workspaces');
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() => _error = AuthService.messageFromDio(e));
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              BrandColors.backgroundDark,
              Color(0xFF1E1B4B),
              BrandColors.primary,
            ],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Column(
                  children: [
                    const WtmLogo(
                      size: 72,
                      showWordmark: true,
                      wordmarkColor: Colors.white,
                    ),
                    const SizedBox(height: 20),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              _step == 0
                                  ? 'Forgot password?'
                                  : _step == 1
                                      ? 'Enter OTP'
                                      : 'New password',
                              style: Theme.of(context)
                                  .textTheme
                                  .headlineMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              _step == 0
                                  ? 'Enter your registered email. We will send a 6-digit code.'
                                  : _step == 1
                                      ? 'We sent a code to ${_emailCtrl.text.trim()}.'
                                      : 'Choose a new password, then you will be signed in.',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(color: AppTheme.slateMuted),
                            ),
                            const SizedBox(height: 20),
                            if (_step == 0)
                              TextField(
                                controller: _emailCtrl,
                                keyboardType: TextInputType.emailAddress,
                                decoration: const InputDecoration(
                                  labelText: 'Email',
                                  prefixIcon: Icon(Icons.email_outlined),
                                ),
                              ),
                            if (_step == 1)
                              TextField(
                                controller: _otpCtrl,
                                keyboardType: TextInputType.number,
                                maxLength: 6,
                                decoration: const InputDecoration(
                                  labelText: 'OTP code',
                                  prefixIcon: Icon(Icons.pin_outlined),
                                ),
                              ),
                            if (_step == 2) ...[
                              TextField(
                                controller: _passCtrl,
                                obscureText: true,
                                decoration: const InputDecoration(
                                  labelText: 'New password',
                                  prefixIcon: Icon(Icons.lock_outline),
                                ),
                              ),
                              const SizedBox(height: 12),
                              TextField(
                                controller: _pass2Ctrl,
                                obscureText: true,
                                decoration: const InputDecoration(
                                  labelText: 'Confirm password',
                                  prefixIcon: Icon(Icons.lock_outline),
                                ),
                              ),
                            ],
                            if (_error != null) ...[
                              const SizedBox(height: 12),
                              Text(
                                _error!,
                                style: const TextStyle(
                                  color: AppTheme.danger,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                            const SizedBox(height: 20),
                            FilledButton(
                              onPressed: _loading
                                  ? null
                                  : () {
                                      if (_step == 0) {
                                        _sendCode();
                                      } else if (_step == 1) {
                                        _continueFromOtp();
                                      } else {
                                        _savePassword();
                                      }
                                    },
                              child: _loading
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : Text(
                                      _step == 0
                                          ? 'Send code'
                                          : _step == 1
                                              ? 'Continue'
                                              : 'Save & sign in',
                                    ),
                            ),
                            const SizedBox(height: 8),
                            TextButton(
                              onPressed: () {
                                if (_step == 0) {
                                  context.go('/login');
                                } else if (_step == 1) {
                                  setState(() {
                                    _step = 0;
                                    _error = null;
                                  });
                                } else {
                                  setState(() {
                                    _step = 1;
                                    _error = null;
                                  });
                                }
                              },
                              child: Text(_step == 0 ? 'Back to sign in' : 'Back'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '© 2026 WorkTaskMe · Powered by lyomastech',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.55),
                        fontSize: 12,
                      ),
                      textAlign: TextAlign.center,
                    ),
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
