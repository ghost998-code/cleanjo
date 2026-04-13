import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../network/api_client.dart';
import '../network/api_endpoints.dart';

class PendingReport {
  final String? localId;
  final double latitude;
  final double longitude;
  final String? address;
  final String? garbageType;
  final String? description;
  final String? imagePath;
  final String severity;
  final DateTime createdAt;

  PendingReport({
    this.localId,
    required this.latitude,
    required this.longitude,
    this.address,
    this.garbageType,
    this.description,
    this.imagePath,
    required this.severity,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
    'local_id': localId,
    'latitude': latitude,
    'longitude': longitude,
    'address': address,
    'garbage_type': garbageType,
    'description': description,
    'image_path': imagePath,
    'severity': severity,
    'created_at': createdAt.toIso8601String(),
  };

  factory PendingReport.fromJson(Map<String, dynamic> json) => PendingReport(
    localId: json['local_id'],
    latitude: json['latitude'],
    longitude: json['longitude'],
    address: json['address'],
    garbageType: json['garbage_type'],
    description: json['description'],
    imagePath: json['image_path'],
    severity: json['severity'],
    createdAt: DateTime.parse(json['created_at']),
  );
}

class SyncService {
  final ApiClient _apiClient;
  final Box _pendingBox = Hive.box('pending_reports');
  
  SyncService(this._apiClient);

  Future<void> queueReport(PendingReport report) async {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    final reportWithId = PendingReport(
      localId: id,
      latitude: report.latitude,
      longitude: report.longitude,
      address: report.address,
      garbageType: report.garbageType,
      description: report.description,
      imagePath: report.imagePath,
      severity: report.severity,
      createdAt: report.createdAt,
    );
    await _pendingBox.put(id, jsonEncode(reportWithId.toJson()));
  }

  Future<void> syncPendingReports() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (!connectivity.contains(ConnectivityResult.none)) {
      final pendingKeys = _pendingBox.keys.toList();
      
      for (final key in pendingKeys) {
        try {
          final data = _pendingBox.get(key);
          if (data == null) continue;
          
          final report = PendingReport.fromJson(jsonDecode(data));
          
          if (report.imagePath != null) {
            await _apiClient.uploadFile(
              ApiEndpoints.reports,
              fields: {
                'latitude': report.latitude.toString(),
                'longitude': report.longitude.toString(),
                'address': report.address ?? '',
                'garbage_type': report.garbageType ?? '',
                'description': report.description ?? '',
                'severity': report.severity,
              },
              filePath: report.imagePath!,
              fileField: 'image',
            );
          } else {
            await _apiClient.post(
              ApiEndpoints.reports,
              data: {
                'latitude': report.latitude,
                'longitude': report.longitude,
                'address': report.address,
                'garbage_type': report.garbageType,
                'description': report.description,
                'severity': report.severity,
              },
            );
          }
          
          await _pendingBox.delete(key);
        } catch (e) {
          // Keep in queue for retry
        }
      }
    }
  }

  int get pendingCount => _pendingBox.length;
}
