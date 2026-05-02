import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:exif/exif.dart';
import 'package:flutter/material.dart';
import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/config/mobile_config_service.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/di/injection.dart';
import '../../../core/inference/on_device_inference_service.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/offline/sync_service.dart';
import '../models/report_draft.dart';

class CreateReportPage extends StatefulWidget {
  const CreateReportPage({super.key});

  @override
  State<CreateReportPage> createState() => _CreateReportPageState();
}

class _CreateReportPageState extends State<CreateReportPage> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();
  final _pendingInferencePaths = <String>{};

  Position? _currentPosition;
  String? _currentAddress;
  ReportDraft _draft = const ReportDraft(
    severity: 'medium',
    description: '',
  );
  bool _isLoading = false;
  bool _isSubmitting = false;
  bool _hasStartedCaptureFlow = false;

  MobileConfigService get _configService => getIt<MobileConfigService>();

  OnDeviceInferenceService get _inferenceService =>
      getIt<OnDeviceInferenceService>();

  int get _maxPhotoCount => _configService.currentConfig.maxReportPhotos;

  bool get _canAddMorePhotos => _draft.photos.length < _maxPhotoCount;

  bool get _hasPhotos => _draft.photos.isNotEmpty;

  bool get _hasPendingInference => _pendingInferencePaths.isNotEmpty;

  bool get _allPhotosHaveInference =>
      _draft.photos.isNotEmpty &&
      _draft.photos.every((photo) => photo.inference != null);

  bool get _hasInferenceFailures => _draft.photos
      .any((photo) => photo.inference == null && photo.inferenceError != null);

  int get _remainingPhotoSlots => _maxPhotoCount - _draft.photos.length;

  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_hasStartedCaptureFlow && mounted) {
        _hasStartedCaptureFlow = true;
        _pickImage(ImageSource.camera);
      }
    });
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _getCurrentLocation() async {
    setState(() => _isLoading = true);

    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.whileInUse ||
          permission == LocationPermission.always) {
        _currentPosition = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
        );

        if (_currentPosition != null) {
          try {
            final placemarks = await placemarkFromCoordinates(
              _currentPosition!.latitude,
              _currentPosition!.longitude,
            );
            if (placemarks.isNotEmpty) {
              final place = placemarks.first;
              _currentAddress = [
                place.street,
                place.locality,
                place.administrativeArea,
              ].where((value) => value != null && value.isNotEmpty).join(', ');
              _draft = _draft.copyWith(address: _currentAddress);
            }
          } catch (_) {}
        }
      }
    } catch (_) {
      _showSnackBar('Could not get location');
    }

    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    if (!_canAddMorePhotos) {
      _showSnackBar('You can add up to $_maxPhotoCount photos');
      return;
    }

    final picker = ImagePicker();
    final position = _currentPosition;
    if (position == null) {
      _showSnackBar('Location is required before adding a photo');
      return;
    }

    if (source == ImageSource.gallery) {
      final pickedFiles = await picker.pickMultiImage(
        maxWidth: 1080,
        maxHeight: 1920,
        imageQuality: 85,
      );
      if (pickedFiles.isEmpty) {
        return;
      }

      final allowedFiles = pickedFiles.take(_remainingPhotoSlots).toList();
      final drafts = <ReportPhotoDraft>[];
      var rejectedForExif = 0;

      for (final pickedFile in allowedFiles) {
        final exifData = await _readGalleryExif(pickedFile.path);
        if (exifData == null) {
          rejectedForExif += 1;
          continue;
        }

        drafts.add(
          ReportPhotoDraft(
            filePath: pickedFile.path,
            sourceType: 'gallery',
            latitude: position.latitude,
            longitude: position.longitude,
            accuracy: position.accuracy,
            capturedAt: exifData.capturedAt ?? DateTime.now().toUtc(),
            exifValidationPassed: true,
            exifLatitude: exifData.latitude,
            exifLongitude: exifData.longitude,
            exifAccuracy: exifData.accuracy,
            exifCapturedAt: exifData.capturedAt,
          ),
        );
      }

      if (drafts.isEmpty) {
        _showSnackBar('Selected gallery photos need GPS EXIF metadata');
        return;
      }

      await _appendPhotos(drafts);
      if (pickedFiles.length > allowedFiles.length) {
        _showSnackBar(
            'Only ${allowedFiles.length} photos were added to stay within the limit');
      } else if (rejectedForExif > 0) {
        _showSnackBar(
            '$rejectedForExif gallery photos were skipped because they have no GPS EXIF');
      }
      return;
    }

    final pickedFile = await picker.pickImage(
      source: source,
      maxWidth: 1080,
      maxHeight: 1920,
      imageQuality: 85,
    );

    if (pickedFile == null) {
      return;
    }

    await _appendPhotos([
      ReportPhotoDraft(
        filePath: pickedFile.path,
        sourceType: 'camera',
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
        capturedAt: DateTime.now().toUtc(),
        exifValidationPassed: true,
      ),
    ]);
  }

  Future<void> _appendPhotos(List<ReportPhotoDraft> photos) async {
    setState(() {
      _draft = _draft.copyWith(photos: [..._draft.photos, ...photos]);
    });

    for (final photo in photos) {
      await _runInferenceForPhoto(photo.filePath);
    }
  }

  Future<void> _runInferenceForPhoto(String filePath) async {
    setState(() {
      _pendingInferencePaths.add(filePath);
      _updatePhotoByPath(
        filePath,
        (photo) =>
            photo.copyWith(clearInference: true, clearInferenceError: true),
      );
    });

    try {
      final inference = await _inferenceService.classifyPhoto(filePath);
      if (!mounted) {
        return;
      }

      setState(() {
        _updatePhotoByPath(
          filePath,
          (photo) =>
              photo.copyWith(inference: inference, clearInferenceError: true),
        );
        _pendingInferencePaths.remove(filePath);
        _recomputeInferenceSummary();
      });
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _updatePhotoByPath(
          filePath,
          (photo) => photo.copyWith(
            clearInference: true,
            inferenceError: 'On-device inference failed for this photo',
          ),
        );
        _pendingInferencePaths.remove(filePath);
        _recomputeInferenceSummary();
      });
    }
  }

  void _updatePhotoByPath(String filePath,
      ReportPhotoDraft Function(ReportPhotoDraft photo) update) {
    final updatedPhotos = _draft.photos.map((photo) {
      if (photo.filePath != filePath) {
        return photo;
      }
      return update(photo);
    }).toList();
    _draft = _draft.copyWith(photos: updatedPhotos);
  }

  void _recomputeInferenceSummary() {
    final summary = _inferenceService.summarize(
      _draft.photos.map((photo) => photo.inference).toList(),
    );
    _draft = _draft.copyWith(
      inferenceSummary: summary,
      clearInferenceSummary: summary == null,
    );
  }

  void _removePhoto(int index) {
    setState(() {
      final removedPhoto = _draft.photos[index];
      _pendingInferencePaths.remove(removedPhoto.filePath);
      final updatedPhotos = [..._draft.photos]..removeAt(index);
      _draft = _draft.copyWith(photos: updatedPhotos);
      _recomputeInferenceSummary();
    });
  }

  List<Map<String, dynamic>> _buildPhotoMetadata() {
    return _draft.photos.map((photo) => photo.toPhotoMetadataJson()).toList();
  }

  Future<void> _submitPhotos(
      ApiClient apiClient, Map<String, dynamic> fields) async {
    final formData = FormData();
    formData.fields.addAll(
      [
        ...fields.entries
            .map((entry) => MapEntry(entry.key, entry.value.toString())),
        MapEntry('photo_metadata', jsonEncode(_buildPhotoMetadata())),
        if (_draft.inferenceSummary != null)
          MapEntry('report_inference_summary',
              jsonEncode(_draft.inferenceSummary!.toJson())),
      ],
    );
    formData.files.addAll(
      await Future.wait(
        _draft.photos.map(
          (photo) => MultipartFile.fromFile(photo.filePath)
              .then((file) => MapEntry('photos', file)),
        ),
      ),
    );

    await apiClient.post(ApiEndpoints.reports, data: formData);
  }

  void _showSnackBar(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _submitReport() async {
    if (!_formKey.currentState!.validate()) return;
    if (_currentPosition == null) {
      _showSnackBar('Location is required');
      return;
    }
    if (!_hasPhotos) {
      _showSnackBar('Add at least one photo before submitting');
      return;
    }
    if (_hasPendingInference) {
      _showSnackBar('Wait for on-device inference to finish for all photos');
      return;
    }
    if (!_allPhotosHaveInference || _hasInferenceFailures) {
      _showSnackBar('Every photo needs a completed on-device inference result');
      return;
    }

    setState(() => _isSubmitting = true);

    final draft = _draft.copyWith(
      category: _draft.category,
      severity: _draft.severity,
      description: _descriptionController.text,
      address: _currentAddress,
    );

    try {
      final apiClient = getIt<ApiClient>();
      final fields = {
        'latitude': _currentPosition!.latitude.toString(),
        'longitude': _currentPosition!.longitude.toString(),
        'address': draft.address ?? '',
        'garbage_type': draft.category ?? '',
        'description': draft.description,
        'severity': draft.severity,
      };

      await _submitPhotos(apiClient, fields);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Report submitted successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop(true);
      }
    } on DioException catch (error) {
      if (!_shouldQueueOffline(error)) {
        _showSnackBar(_parseSubmitError(error));
      } else {
        final syncService = getIt<SyncService>();
        await syncService.queueReport(
          PendingReport(
            draft: draft,
            latitude: _currentPosition!.latitude,
            longitude: _currentPosition!.longitude,
            createdAt: DateTime.now(),
          ),
        );

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Report saved offline. Will sync when connected.'),
              backgroundColor: Colors.orange,
            ),
          );
          Navigator.of(context).pop(true);
        }
      }
    } catch (_) {
      final syncService = getIt<SyncService>();
      await syncService.queueReport(
        PendingReport(
          draft: draft,
          latitude: _currentPosition!.latitude,
          longitude: _currentPosition!.longitude,
          createdAt: DateTime.now(),
        ),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Report saved offline. Will sync when connected.'),
            backgroundColor: Colors.orange,
          ),
        );
        Navigator.of(context).pop(true);
      }
    }

    if (mounted) {
      setState(() => _isSubmitting = false);
    }
  }

  bool _shouldQueueOffline(DioException error) {
    if (error.response != null) {
      return false;
    }

    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.unknown;
  }

  String _parseSubmitError(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.isNotEmpty) {
        return detail;
      }
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map<String, dynamic>) {
          final message = first['msg'] as String?;
          if (message != null && message.isNotEmpty) {
            final loc = (first['loc'] as List?)
                    ?.whereType<Object>()
                    .map((value) => value.toString())
                    .join(' -> ') ??
                'request';
            return '$loc: $message';
          }
        }
      }
    }

    if (error.response?.statusCode == 401) {
      return 'Your session expired. Please sign in again.';
    }

    return 'Report submission failed. Please try again.';
  }

  Future<_GalleryExifData?> _readGalleryExif(String filePath) async {
    try {
      final tags = await readExifFromBytes(await File(filePath).readAsBytes());
      final latitude =
          _parseExifCoordinate(tags, 'GPS GPSLatitude', 'GPS GPSLatitudeRef');
      final longitude =
          _parseExifCoordinate(tags, 'GPS GPSLongitude', 'GPS GPSLongitudeRef');
      if (latitude == null || longitude == null) {
        return null;
      }

      final capturedAt = _parseExifDateTime(tags);
      return _GalleryExifData(
        latitude: latitude,
        longitude: longitude,
        accuracy: null,
        capturedAt: capturedAt,
      );
    } catch (_) {
      return null;
    }
  }

  double? _parseExifCoordinate(
      Map<String, IfdTag> tags, String key, String refKey) {
    final value = tags[key]?.printable;
    final ref = tags[refKey]?.printable;
    if (value == null || ref == null) {
      return null;
    }

    final parts = RegExp(r'-?\d+(?:\.\d+)?').allMatches(value).map((match) {
      return double.parse(match.group(0)!);
    }).toList();
    if (parts.length < 3) {
      return null;
    }

    var decimal = parts[0] + (parts[1] / 60) + (parts[2] / 3600);
    if (ref.toUpperCase() == 'S' || ref.toUpperCase() == 'W') {
      decimal *= -1;
    }
    return decimal;
  }

  DateTime? _parseExifDateTime(Map<String, IfdTag> tags) {
    final raw = tags['EXIF DateTimeOriginal']?.printable ??
        tags['Image DateTime']?.printable;
    if (raw == null || raw.isEmpty) {
      return null;
    }

    final normalized = raw.replaceFirstMapped(
      RegExp(r'^(\d{4}):(\d{2}):(\d{2})'),
      (match) => '${match.group(1)}-${match.group(2)}-${match.group(3)}',
    );
    return DateTime.tryParse(normalized)?.toUtc();
  }

  String _formatConfidence(double value) =>
      '${(value * 100).toStringAsFixed(0)}%';

  Widget _buildInferenceBadge(ReportPhotoDraft photo) {
    if (_pendingInferencePaths.contains(photo.filePath)) {
      return const _PhotoStatusBadge(
        icon: Icons.hourglass_top,
        label: 'Running on-device inference',
        backgroundColor: Color(0xCC1E3A5F),
      );
    }

    if (photo.inferenceError != null) {
      return _PhotoStatusBadge(
        icon: Icons.error_outline,
        label: photo.inferenceError!,
        backgroundColor: const Color(0xCC7F1D1D),
      );
    }

    final inference = photo.inference;
    if (inference == null) {
      return const _PhotoStatusBadge(
        icon: Icons.info_outline,
        label: 'Inference pending',
        backgroundColor: Color(0xCC374151),
      );
    }

    final severity = inference.predictedSeverity;
    final text = severity == null
        ? '${inference.predictedCategory} ${_formatConfidence(inference.predictionConfidence)}'
        : '${inference.predictedCategory} ${_formatConfidence(inference.predictionConfidence)} • $severity';
    return _PhotoStatusBadge(
      icon: Icons.memory,
      label: text,
      backgroundColor: const Color(0xCC14532D),
    );
  }

  @override
  Widget build(BuildContext context) {
    final summary = _draft.inferenceSummary;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Garbage'),
        actions: [
          if (getIt<SyncService>().pendingCount > 0)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Chip(
                label: Text('${getIt<SyncService>().pendingCount} pending'),
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    GestureDetector(
                      onTap: _showImageSourceDialog,
                      child: Container(
                        constraints: const BoxConstraints(minHeight: 200),
                        decoration: BoxDecoration(
                          color: Colors.grey[200],
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.grey[400]!),
                        ),
                        child: _hasPhotos
                            ? Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                        16, 16, 16, 8),
                                    child: Row(
                                      children: [
                                        const Icon(
                                            Icons.photo_library_outlined),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            '${_draft.photos.length} / $_maxPhotoCount photos',
                                            style: const TextStyle(
                                                fontWeight: FontWeight.w600),
                                          ),
                                        ),
                                        if (_canAddMorePhotos)
                                          TextButton.icon(
                                            onPressed: _showImageSourceDialog,
                                            icon: const Icon(Icons.add),
                                            label: const Text('Add more'),
                                          ),
                                      ],
                                    ),
                                  ),
                                  SizedBox(
                                    height: 212,
                                    child: ListView.separated(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 16),
                                      scrollDirection: Axis.horizontal,
                                      itemBuilder: (context, index) {
                                        final photo = _draft.photos[index];
                                        return SizedBox(
                                          width: 190,
                                          child: Stack(
                                            children: [
                                              Positioned.fill(
                                                child: ClipRRect(
                                                  borderRadius:
                                                      BorderRadius.circular(12),
                                                  child: Image.file(
                                                    File(photo.filePath),
                                                    fit: BoxFit.cover,
                                                  ),
                                                ),
                                              ),
                                              Positioned(
                                                top: 8,
                                                right: 8,
                                                child: CircleAvatar(
                                                  radius: 18,
                                                  backgroundColor:
                                                      Colors.black54,
                                                  child: IconButton(
                                                    padding: EdgeInsets.zero,
                                                    iconSize: 18,
                                                    color: Colors.white,
                                                    icon:
                                                        const Icon(Icons.close),
                                                    onPressed: () =>
                                                        _removePhoto(index),
                                                  ),
                                                ),
                                              ),
                                              Positioned(
                                                left: 8,
                                                top: 8,
                                                child: _PhotoStatusBadge(
                                                  icon: photo.sourceType ==
                                                          'camera'
                                                      ? Icons
                                                          .camera_alt_outlined
                                                      : Icons
                                                          .photo_library_outlined,
                                                  label: photo.sourceType ==
                                                          'camera'
                                                      ? 'Camera'
                                                      : 'Gallery',
                                                  backgroundColor:
                                                      const Color(0xCC111827),
                                                ),
                                              ),
                                              Positioned(
                                                  left: 8,
                                                  right: 8,
                                                  bottom: 8,
                                                  child: _buildInferenceBadge(
                                                      photo)),
                                            ],
                                          ),
                                        );
                                      },
                                      separatorBuilder: (_, __) =>
                                          const SizedBox(width: 12),
                                      itemCount: _draft.photos.length,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                ],
                              )
                            : Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.add_a_photo,
                                      size: 48, color: Colors.grey[600]),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Tap to add your first photo',
                                    style: TextStyle(color: Colors.grey[600]),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Camera opens first, gallery photos need GPS EXIF',
                                    style: TextStyle(
                                        color: Colors.grey[600], fontSize: 12),
                                  ),
                                ],
                              ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (summary != null)
                      Card(
                        color: const Color(0xFFF0FDF4),
                        child: ListTile(
                          leading: const Icon(Icons.auto_awesome,
                              color: Color(0xFF166534)),
                          title: Text(
                              'Device summary: ${summary.summaryCategory}'),
                          subtitle: Text(
                            '${_formatConfidence(summary.summaryConfidence)} confidence • ${summary.summaryStrategy}',
                          ),
                        ),
                      ),
                    if (_hasPendingInference)
                      const Padding(
                        padding: EdgeInsets.only(bottom: 16),
                        child: LinearProgressIndicator(),
                      ),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Row(
                          children: [
                            Icon(
                              Icons.location_on,
                              color: _currentPosition != null
                                  ? Colors.green
                                  : Colors.grey,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _currentPosition != null
                                        ? 'Location captured'
                                        : 'Getting location...',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.bold),
                                  ),
                                  if (_currentAddress != null)
                                    Text(
                                      _currentAddress!,
                                      style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey[600]),
                                    ),
                                  if (_currentPosition != null)
                                    Text(
                                      '${_currentPosition!.latitude.toStringAsFixed(6)}, ${_currentPosition!.longitude.toStringAsFixed(6)}',
                                      style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey[600]),
                                    ),
                                ],
                              ),
                            ),
                            IconButton(
                                icon: const Icon(Icons.refresh),
                                onPressed: _getCurrentLocation),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _draft.category,
                      decoration: const InputDecoration(
                        labelText: 'Garbage Type',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.category),
                      ),
                      items: AppConstants.garbageTypes
                          .map(
                            (type) => DropdownMenuItem(
                              value: type,
                              child: Text(
                                  type[0].toUpperCase() + type.substring(1)),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        setState(() {
                          _draft = _draft.copyWith(category: value);
                        });
                      },
                    ),
                    const SizedBox(height: 16),
                    const Text('Severity Level'),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children:
                          AppConstants.severityLabels.entries.map((entry) {
                        final isSelected = _draft.severity == entry.key;
                        return ChoiceChip(
                          label: Text(entry.value),
                          selected: isSelected,
                          selectedColor: Color(
                              AppConstants.severityColors[entry.key] ??
                                  0xFF9E9E9E),
                          onSelected: (selected) {
                            if (selected) {
                              setState(() {
                                _draft = _draft.copyWith(severity: entry.key);
                              });
                            }
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _descriptionController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Description (optional)',
                        border: OutlineInputBorder(),
                        hintText: 'Add any additional details...',
                      ),
                    ),
                    if (_hasInferenceFailures)
                      const Padding(
                        padding: EdgeInsets.only(top: 12),
                        child: Text(
                          'Retry or replace any photo with a failed inference result before submitting.',
                          style: TextStyle(color: Color(0xFFB45309)),
                        ),
                      ),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed:
                          _isSubmitting || !_hasPhotos || _hasPendingInference
                              ? null
                              : _submitReport,
                      icon: _isSubmitting
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.send),
                      label: Text(
                        _isSubmitting
                            ? 'Submitting...'
                            : _hasPendingInference
                                ? 'Waiting for inference...'
                                : _hasPhotos
                                    ? 'Submit Report'
                                    : 'Add a photo to continue',
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Take Photo'),
              subtitle: Text(
                  'Add 1 photo (${_draft.photos.length}/$_maxPhotoCount used)'),
              enabled: _canAddMorePhotos,
              onTap: () {
                Navigator.pop(context);
                if (_canAddMorePhotos) {
                  _pickImage(ImageSource.camera);
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Choose from Gallery'),
              subtitle: Text('Add up to $_remainingPhotoSlots more'),
              enabled: _canAddMorePhotos,
              onTap: () {
                Navigator.pop(context);
                if (_canAddMorePhotos) {
                  _pickImage(ImageSource.gallery);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _PhotoStatusBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color backgroundColor;

  const _PhotoStatusBadge({
    required this.icon,
    required this.label,
    required this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: Colors.white),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GalleryExifData {
  final double latitude;
  final double longitude;
  final double? accuracy;
  final DateTime? capturedAt;

  const _GalleryExifData({
    required this.latitude,
    required this.longitude,
    required this.accuracy,
    required this.capturedAt,
  });
}
