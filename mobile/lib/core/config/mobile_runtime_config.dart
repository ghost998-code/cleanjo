class MobileRuntimeConfig {
  final int maxReportPhotos;
  final double gpsMaxAccuracyMeters;

  const MobileRuntimeConfig({
    required this.maxReportPhotos,
    required this.gpsMaxAccuracyMeters,
  });

  static const fallback = MobileRuntimeConfig(
    maxReportPhotos: 15,
    gpsMaxAccuracyMeters: 10,
  );

  Map<String, dynamic> toJson() => {
        'max_report_photos': maxReportPhotos,
        'gps_max_accuracy_meters': gpsMaxAccuracyMeters,
      };

  factory MobileRuntimeConfig.fromJson(Map<String, dynamic> json) {
    return MobileRuntimeConfig(
      maxReportPhotos: (json['max_report_photos'] as num).toInt(),
      gpsMaxAccuracyMeters: (json['gps_max_accuracy_meters'] as num).toDouble(),
    );
  }
}
