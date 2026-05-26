import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      // Replace with your backend base URL (e.g. FastAPI on http://10.0.2.2:8000 for Android emulator).
      baseUrl: 'http://localhost:8000',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );
  return dio;
});
