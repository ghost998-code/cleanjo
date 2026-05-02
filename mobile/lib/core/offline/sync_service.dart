import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import '../../features/citizen/models/report_draft.dart';

class PendingReport {
  final String? localId;
  final ReportDraft draft;
  final double latitude;
  final double longitude;
  final DateTime createdAt;
  final String syncStatus;
  final String? lastError;

  PendingReport({
    this.localId,
    required this.draft,
    required this.latitude,
    required this.longitude,
    required this.createdAt,
    this.syncStatus = 'pending',
    this.lastError,
  });

  PendingReport copyWith({
    String? localId,
    ReportDraft? draft,
    double? latitude,
    double? longitude,
    DateTime? createdAt,
    String? syncStatus,
    String? lastError,
    bool clearLastError = false,
  }) {
    return PendingReport(
      localId: localId ?? this.localId,
      draft: draft ?? this.draft,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      createdAt: createdAt ?? this.createdAt,
      syncStatus: syncStatus ?? this.syncStatus,
      lastError: clearLastError ? null : (lastError ?? this.lastError),
    );
  }

  Map<String, dynamic> toJson() => {
        'local_id': localId,
        'draft': draft.toJson(),
        'latitude': latitude,
        'longitude': longitude,
        'created_at': createdAt.toIso8601String(),
        'sync_status': syncStatus,
        'last_error': lastError,
      };

  factory PendingReport.fromJson(Map<String, dynamic> json) => PendingReport(
        localId: json['local_id'],
        draft: ReportDraft.fromJson(
            Map<String, dynamic>.from(json['draft'] as Map)),
        latitude: json['latitude'],
        longitude: json['longitude'],
        createdAt: DateTime.parse(json['created_at']),
        syncStatus: json['sync_status'] as String? ?? 'pending',
        lastError: json['last_error'] as String?,
      );
}

class SyncService {
  final ApiClient _apiClient;
  final Box _pendingBox = Hive.box('pending_reports');
  StreamSubscription<ConnectivityResult>? _connectivitySubscription;
  bool _started = false;

  SyncService(this._apiClient);

  Future<void> start() async {
    if (_started) {
      return;
    }
    _started = true;

    await syncPendingReports();
    _connectivitySubscription = Connectivity().onConnectivityChanged.listen((
      connectivity,
    ) {
      if (connectivity != ConnectivityResult.none) {
        syncPendingReports();
      }
    });
  }

  Future<void> stop() async {
    await _connectivitySubscription?.cancel();
    _connectivitySubscription = null;
    _started = false;
  }

  Future<void> queueReport(PendingReport report) async {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    final reportWithId = PendingReport(
      localId: id,
      draft: report.draft,
      latitude: report.latitude,
      longitude: report.longitude,
      createdAt: report.createdAt,
      syncStatus: 'pending',
    );
    await _pendingBox.put(id, jsonEncode(reportWithId.toJson()));
  }

  Future<void> _saveReport(String key, PendingReport report) async {
    await _pendingBox.put(key, jsonEncode(report.toJson()));
  }

  bool _isRetryable(DioException error) {
    return error.response == null || (error.response!.statusCode ?? 0) >= 500;
  }

  String _extractSyncError(Object error) {
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map<String, dynamic>) {
        final detail = data['detail'];
        if (detail is String && detail.isNotEmpty) {
          return detail;
        }
        if (detail is List && detail.isNotEmpty) {
          final first = detail.first;
          if (first is Map) {
            final loc = (first['loc'] as List?)
                    ?.whereType<Object>()
                    .map((value) => value.toString())
                    .join(' -> ') ??
                'request';
            final message = first['msg'] as String?;
            if (message != null && message.isNotEmpty) {
              return '$loc: $message';
            }
          }
        }
      }

      if (error.response?.statusCode == 401) {
        return 'Your session expired. Please sign in again.';
      }
    }

    return error.toString();
  }

  Future<FormData> _buildFormData(PendingReport report) async {
    final fields = {
      'latitude': report.latitude.toString(),
      'longitude': report.longitude.toString(),
      'address': report.draft.address ?? '',
      'garbage_type': report.draft.category ?? '',
      'description': report.draft.description,
      'severity': report.draft.severity,
      'photo_metadata': jsonEncode(
        report.draft.photos
            .map((photo) => photo.toPhotoMetadataJson())
            .toList(),
      ),
    };

    final summary = report.draft.inferenceSummary;
    if (summary != null) {
      fields['report_inference_summary'] = jsonEncode(summary.toJson());
    }

    final formData = FormData();
    formData.fields.addAll(
        fields.entries.map((entry) => MapEntry(entry.key, entry.value)));
    formData.files.addAll(
      await Future.wait(
        report.draft.photos.map((photo) async {
          if (!await File(photo.filePath).exists()) {
            throw StateError('Photo file missing for offline report sync');
          }
          return MapEntry(
              'photos', await MultipartFile.fromFile(photo.filePath));
        }),
      ),
    );
    return formData;
  }

  Future<void> syncPendingReports() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity != ConnectivityResult.none) {
      final pendingKeys = _pendingBox.keys.toList();

      for (final key in pendingKeys) {
        try {
          final data = _pendingBox.get(key);
          if (data == null) continue;

          final report = PendingReport.fromJson(
            Map<String, dynamic>.from(jsonDecode(data as String) as Map),
          );
          if (report.syncStatus != 'pending') {
            continue;
          }
          if (report.draft.photos.isEmpty) {
            await _saveReport(
              key.toString(),
              report.copyWith(
                syncStatus: 'failed',
                lastError:
                    'This offline report has no photos and cannot be synced. Please resubmit it.',
              ),
            );
            continue;
          }

          final formData = await _buildFormData(report);
          await _apiClient.post(ApiEndpoints.reports, data: formData);

          await _pendingBox.delete(key);
        } on DioException catch (error) {
          if (_isRetryable(error)) {
            continue;
          }

          final data = _pendingBox.get(key);
          if (data == null) {
            continue;
          }
          final report = PendingReport.fromJson(
            Map<String, dynamic>.from(jsonDecode(data as String) as Map),
          );
          await _saveReport(
            key.toString(),
            report.copyWith(
              syncStatus: 'failed',
              lastError: _extractSyncError(error),
            ),
          );
        } catch (error) {
          final data = _pendingBox.get(key);
          if (data == null) {
            continue;
          }
          final report = PendingReport.fromJson(
            Map<String, dynamic>.from(jsonDecode(data as String) as Map),
          );
          await _saveReport(
            key.toString(),
            report.copyWith(
              syncStatus: 'failed',
              lastError: _extractSyncError(error),
            ),
          );
        }
      }
    }
  }

  List<PendingReport> getPendingReports() {
    return _pendingBox.values
        .map((data) {
          try {
            return PendingReport.fromJson(
              Map<String, dynamic>.from(jsonDecode(data as String) as Map),
            );
          } catch (_) {
            return null;
          }
        })
        .whereType<PendingReport>()
        .toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
  }

  int get pendingCount => getPendingReports()
      .where((report) => report.syncStatus == 'pending')
      .length;
}
