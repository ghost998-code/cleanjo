import 'dart:io';

import 'package:image/image.dart' as img;

const _supportedCategories = <String>[
  'household',
  'construction',
  'green',
  'hazardous',
  'electronic',
  'bulky',
  'mixed',
  'other',
];

class InferencePredictionDraft {
  final String label;
  final double confidence;

  const InferencePredictionDraft({
    required this.label,
    required this.confidence,
  });

  Map<String, dynamic> toJson() => {
        'label': label,
        'confidence': confidence,
      };

  factory InferencePredictionDraft.fromJson(Map<String, dynamic> json) {
    return InferencePredictionDraft(
      label: json['label'] as String,
      confidence: (json['confidence'] as num).toDouble(),
    );
  }
}

class PhotoInferenceDraft {
  final String predictedCategory;
  final double predictionConfidence;
  final String? predictedSeverity;
  final double? severityConfidence;
  final List<InferencePredictionDraft> topPredictions;
  final String modelName;
  final String modelVersion;
  final DateTime inferenceRanAt;
  final String inferenceSource;

  const PhotoInferenceDraft({
    required this.predictedCategory,
    required this.predictionConfidence,
    required this.topPredictions,
    required this.modelName,
    required this.modelVersion,
    required this.inferenceRanAt,
    this.predictedSeverity,
    this.severityConfidence,
    this.inferenceSource = 'mobile',
  });

  Map<String, dynamic> toJson() => {
        'predicted_category': predictedCategory,
        'prediction_confidence': predictionConfidence,
        'predicted_severity': predictedSeverity,
        'severity_confidence': severityConfidence,
        'top_predictions':
            topPredictions.map((prediction) => prediction.toJson()).toList(),
        'model_name': modelName,
        'model_version': modelVersion,
        'inference_ran_at': inferenceRanAt.toIso8601String(),
        'inference_source': inferenceSource,
      };

  factory PhotoInferenceDraft.fromJson(Map<String, dynamic> json) {
    return PhotoInferenceDraft(
      predictedCategory: json['predicted_category'] as String,
      predictionConfidence: (json['prediction_confidence'] as num).toDouble(),
      predictedSeverity: json['predicted_severity'] as String?,
      severityConfidence: (json['severity_confidence'] as num?)?.toDouble(),
      topPredictions: ((json['top_predictions'] as List?) ?? const [])
          .whereType<Map>()
          .map((prediction) => InferencePredictionDraft.fromJson(
              Map<String, dynamic>.from(prediction)))
          .toList(),
      modelName: json['model_name'] as String,
      modelVersion: json['model_version'] as String,
      inferenceRanAt: DateTime.parse(json['inference_ran_at'] as String),
      inferenceSource: json['inference_source'] as String? ?? 'mobile',
    );
  }
}

class ReportInferenceSummaryDraft {
  final String summaryCategory;
  final double summaryConfidence;
  final String summaryStrategy;
  final int derivedFromPhotoCount;
  final String modelVersion;

  const ReportInferenceSummaryDraft({
    required this.summaryCategory,
    required this.summaryConfidence,
    required this.summaryStrategy,
    required this.derivedFromPhotoCount,
    required this.modelVersion,
  });

  Map<String, dynamic> toJson() => {
        'summary_category': summaryCategory,
        'summary_confidence': summaryConfidence,
        'summary_strategy': summaryStrategy,
        'derived_from_photo_count': derivedFromPhotoCount,
        'model_version': modelVersion,
      };

  factory ReportInferenceSummaryDraft.fromJson(Map<String, dynamic> json) {
    return ReportInferenceSummaryDraft(
      summaryCategory: json['summary_category'] as String,
      summaryConfidence: (json['summary_confidence'] as num).toDouble(),
      summaryStrategy: json['summary_strategy'] as String,
      derivedFromPhotoCount: json['derived_from_photo_count'] as int,
      modelVersion: json['model_version'] as String,
    );
  }
}

class OnDeviceInferenceService {
  static const modelName = 'device_color_profile_classifier';
  static const modelVersion = '0.1.0';

  Future<PhotoInferenceDraft> classifyPhoto(String filePath) async {
    final imageBytes = await File(filePath).readAsBytes();
    final decodedImage = img.decodeImage(imageBytes);
    if (decodedImage == null) {
      throw StateError('Could not decode image for on-device inference');
    }

    final resized = img.copyResize(decodedImage, width: 64);

    double red = 0;
    double green = 0;
    double blue = 0;
    double brightness = 0;
    double contrast = 0;
    double minLuma = 255;
    double maxLuma = 0;

    for (final pixel in resized) {
      red += pixel.r;
      green += pixel.g;
      blue += pixel.b;
      final luma = (0.299 * pixel.r) + (0.587 * pixel.g) + (0.114 * pixel.b);
      brightness += luma;
      if (luma < minLuma) minLuma = luma;
      if (luma > maxLuma) maxLuma = luma;
    }

    final pixelCount = resized.width * resized.height;
    red /= pixelCount;
    green /= pixelCount;
    blue /= pixelCount;
    brightness /= pixelCount;
    contrast = (maxLuma - minLuma) / 255;

    final totalColor = (red + green + blue).clamp(1, double.infinity);
    final redRatio = red / totalColor;
    final greenRatio = green / totalColor;
    final blueRatio = blue / totalColor;
    final brightnessRatio = brightness / 255;

    final rawScores = <String, double>{
      'green': 0.12 + (greenRatio * 0.9) + ((1 - brightnessRatio) * 0.1),
      'hazardous': 0.08 + (redRatio * 0.95) + (contrast * 0.2),
      'electronic': 0.08 + (blueRatio * 0.9) + (contrast * 0.15),
      'construction':
          0.08 + ((redRatio + greenRatio) * 0.35) + ((1 - blueRatio) * 0.4),
      'household': 0.1 + (brightnessRatio * 0.35) + ((1 - contrast) * 0.25),
      'bulky': 0.08 + ((1 - contrast) * 0.45) + ((1 - brightnessRatio) * 0.2),
      'mixed': 0.12 + (contrast * 0.55),
      'other': 0.08 + ((1 - (redRatio - greenRatio).abs()) * 0.15),
    };

    final totalScore =
        rawScores.values.fold<double>(0, (sum, value) => sum + value);
    final normalizedEntries = rawScores.entries
        .map((entry) => MapEntry(entry.key, entry.value / totalScore))
        .toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final predicted = normalizedEntries.first;
    final predictedSeverity =
        _severityFor(predicted.key, predicted.value, brightnessRatio);
    final severityConfidence = (predicted.value * 0.9).clamp(0.0, 1.0);

    return PhotoInferenceDraft(
      predictedCategory: predicted.key,
      predictionConfidence: predicted.value.clamp(0.0, 1.0),
      predictedSeverity: predictedSeverity,
      severityConfidence: severityConfidence,
      topPredictions: normalizedEntries
          .take(3)
          .map(
            (entry) => InferencePredictionDraft(
              label: entry.key,
              confidence: entry.value.clamp(0.0, 1.0),
            ),
          )
          .toList(),
      modelName: modelName,
      modelVersion: modelVersion,
      inferenceRanAt: DateTime.now().toUtc(),
    );
  }

  ReportInferenceSummaryDraft? summarize(
      List<PhotoInferenceDraft?> photoInferences) {
    final completedInferences =
        photoInferences.whereType<PhotoInferenceDraft>().toList();
    if (completedInferences.isEmpty) {
      return null;
    }

    completedInferences.sort(
      (a, b) => b.predictionConfidence.compareTo(a.predictionConfidence),
    );
    final winner = completedInferences.first;

    return ReportInferenceSummaryDraft(
      summaryCategory: winner.predictedCategory,
      summaryConfidence: winner.predictionConfidence,
      summaryStrategy: 'highest_confidence_photo',
      derivedFromPhotoCount: completedInferences.length,
      modelVersion: winner.modelVersion,
    );
  }

  String _severityFor(
      String category, double confidence, double brightnessRatio) {
    if (category == 'hazardous' && confidence >= 0.2) {
      return 'critical';
    }
    if (category == 'mixed' || category == 'construction') {
      return confidence >= 0.18 ? 'high' : 'medium';
    }
    if (category == 'bulky' || brightnessRatio < 0.3) {
      return 'medium';
    }
    return confidence >= 0.22 ? 'medium' : 'low';
  }

  bool isSupportedCategory(String value) =>
      _supportedCategories.contains(value);
}
