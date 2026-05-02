import '../../../core/inference/on_device_inference_service.dart';

class ReportPhotoDraft {
  final String filePath;
  final String sourceType;
  final double latitude;
  final double longitude;
  final double accuracy;
  final DateTime capturedAt;
  final bool exifValidationPassed;
  final double? exifLatitude;
  final double? exifLongitude;
  final double? exifAccuracy;
  final DateTime? exifCapturedAt;
  final PhotoInferenceDraft? inference;
  final String? inferenceError;

  const ReportPhotoDraft({
    required this.filePath,
    required this.sourceType,
    required this.latitude,
    required this.longitude,
    required this.accuracy,
    required this.capturedAt,
    required this.exifValidationPassed,
    this.exifLatitude,
    this.exifLongitude,
    this.exifAccuracy,
    this.exifCapturedAt,
    this.inference,
    this.inferenceError,
  });

  ReportPhotoDraft copyWith({
    String? filePath,
    String? sourceType,
    double? latitude,
    double? longitude,
    double? accuracy,
    DateTime? capturedAt,
    bool? exifValidationPassed,
    double? exifLatitude,
    double? exifLongitude,
    double? exifAccuracy,
    DateTime? exifCapturedAt,
    PhotoInferenceDraft? inference,
    String? inferenceError,
    bool clearInference = false,
    bool clearInferenceError = false,
  }) {
    return ReportPhotoDraft(
      filePath: filePath ?? this.filePath,
      sourceType: sourceType ?? this.sourceType,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      accuracy: accuracy ?? this.accuracy,
      capturedAt: capturedAt ?? this.capturedAt,
      exifValidationPassed: exifValidationPassed ?? this.exifValidationPassed,
      exifLatitude: exifLatitude ?? this.exifLatitude,
      exifLongitude: exifLongitude ?? this.exifLongitude,
      exifAccuracy: exifAccuracy ?? this.exifAccuracy,
      exifCapturedAt: exifCapturedAt ?? this.exifCapturedAt,
      inference: clearInference ? null : (inference ?? this.inference),
      inferenceError:
          clearInferenceError ? null : (inferenceError ?? this.inferenceError),
    );
  }

  Map<String, dynamic> toPhotoMetadataJson() => {
        'source_type': sourceType,
        'latitude': latitude,
        'longitude': longitude,
        'gps_accuracy': accuracy,
        'captured_at': capturedAt.toIso8601String(),
        'exif_latitude': exifLatitude,
        'exif_longitude': exifLongitude,
        'exif_accuracy': exifAccuracy,
        'exif_captured_at': exifCapturedAt?.toIso8601String(),
        ...?inference?.toJson(),
      };

  Map<String, dynamic> toJson() => {
        'file_path': filePath,
        'source_type': sourceType,
        'latitude': latitude,
        'longitude': longitude,
        'accuracy': accuracy,
        'captured_at': capturedAt.toIso8601String(),
        'exif_validation_passed': exifValidationPassed,
        'exif_latitude': exifLatitude,
        'exif_longitude': exifLongitude,
        'exif_accuracy': exifAccuracy,
        'exif_captured_at': exifCapturedAt?.toIso8601String(),
        'inference': inference?.toJson(),
        'inference_error': inferenceError,
      };

  factory ReportPhotoDraft.fromJson(Map<String, dynamic> json) {
    return ReportPhotoDraft(
      filePath: json['file_path'] as String,
      sourceType: json['source_type'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      accuracy: (json['accuracy'] as num).toDouble(),
      capturedAt: DateTime.parse(json['captured_at'] as String),
      exifValidationPassed: json['exif_validation_passed'] as bool? ?? false,
      exifLatitude: (json['exif_latitude'] as num?)?.toDouble(),
      exifLongitude: (json['exif_longitude'] as num?)?.toDouble(),
      exifAccuracy: (json['exif_accuracy'] as num?)?.toDouble(),
      exifCapturedAt: json['exif_captured_at'] != null
          ? DateTime.parse(json['exif_captured_at'] as String)
          : null,
      inference: json['inference'] is Map<String, dynamic>
          ? PhotoInferenceDraft.fromJson(
              json['inference'] as Map<String, dynamic>)
          : json['inference'] is Map
              ? PhotoInferenceDraft.fromJson(
                  Map<String, dynamic>.from(json['inference'] as Map))
              : null,
      inferenceError: json['inference_error'] as String?,
    );
  }
}

class ReportDraft {
  final String? category;
  final String severity;
  final String description;
  final String? address;
  final List<ReportPhotoDraft> photos;
  final ReportInferenceSummaryDraft? inferenceSummary;

  const ReportDraft({
    this.category,
    required this.severity,
    required this.description,
    this.address,
    this.photos = const [],
    this.inferenceSummary,
  });

  ReportDraft copyWith({
    String? category,
    String? severity,
    String? description,
    String? address,
    List<ReportPhotoDraft>? photos,
    ReportInferenceSummaryDraft? inferenceSummary,
    bool clearInferenceSummary = false,
  }) {
    return ReportDraft(
      category: category ?? this.category,
      severity: severity ?? this.severity,
      description: description ?? this.description,
      address: address ?? this.address,
      photos: photos ?? this.photos,
      inferenceSummary: clearInferenceSummary
          ? null
          : (inferenceSummary ?? this.inferenceSummary),
    );
  }

  Map<String, dynamic> toJson() => {
        'category': category,
        'severity': severity,
        'description': description,
        'address': address,
        'photos': photos.map((photo) => photo.toJson()).toList(),
        'inference_summary': inferenceSummary?.toJson(),
      };

  factory ReportDraft.fromJson(Map<String, dynamic> json) {
    return ReportDraft(
      category: json['category'] as String?,
      severity: json['severity'] as String,
      description: json['description'] as String? ?? '',
      address: json['address'] as String?,
      photos: ((json['photos'] as List?) ?? const [])
          .whereType<Map>()
          .map((photo) =>
              ReportPhotoDraft.fromJson(Map<String, dynamic>.from(photo)))
          .toList(),
      inferenceSummary: json['inference_summary'] is Map<String, dynamic>
          ? ReportInferenceSummaryDraft.fromJson(
              json['inference_summary'] as Map<String, dynamic>)
          : json['inference_summary'] is Map
              ? ReportInferenceSummaryDraft.fromJson(
                  Map<String, dynamic>.from(json['inference_summary'] as Map))
              : null,
    );
  }
}
