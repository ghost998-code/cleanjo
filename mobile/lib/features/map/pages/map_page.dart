import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/di/injection.dart';
import '../../../core/constants/app_constants.dart';

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  static const LatLng _defaultCenter = LatLng(31.9539, 35.9106);

  GoogleMapController? _mapController;
  List<_ReportMarker> _markers = [];
  bool _isLoading = true;
  bool _isLocatingUser = false;
  bool _hasLocationPermission = false;
  String? _selectedStatus;
  LatLng _currentCenter = _defaultCenter;
  LatLng? _userLocation;

  @override
  void initState() {
    super.initState();
    _fetchMarkers();
    _initializeUserLocation();
  }

  Future<void> _initializeUserLocation() async {
    await _getCurrentLocation();
  }

  Future<void> _fetchMarkers() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = getIt<ApiClient>();
      final queryParams = <String, dynamic>{};
      if (_selectedStatus != null) {
        queryParams['status'] = _selectedStatus;
      }

      List<_ReportMarker> markers = const [];

      try {
        final response = await apiClient.get(
          ApiEndpoints.reportsMap,
          queryParameters: queryParams,
        );
        markers = _parseMarkers(response.data);
      } catch (_) {
        final response = await apiClient.get(
          ApiEndpoints.reports,
          queryParameters: queryParams,
        );
        markers = _parseMarkers(response.data);
      }

      setState(() {
        _markers = markers;
        _isLoading = false;
      });
      await _fitMapToMarkers(markers);
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  List<_ReportMarker> _parseMarkers(dynamic data) {
    final markerData = switch (data) {
      {'features': final List features} => features,
      {'items': final List items} => items,
      final List items => items,
      _ => const [],
    };

    return markerData
        .map<_ReportMarker?>((item) {
          if (item is! Map<String, dynamic>) {
            return null;
          }

          final geoJsonMarker = _parseGeoJsonMarker(item);
          if (geoJsonMarker != null) {
            return geoJsonMarker;
          }

          return _parseReportMarker(item);
        })
        .whereType<_ReportMarker>()
        .toList();
  }

  _ReportMarker? _parseGeoJsonMarker(Map<String, dynamic> feature) {
    final geometry = feature['geometry'];
    final properties = feature['properties'];
    if (geometry is! Map<String, dynamic> || properties is! Map<String, dynamic>) {
      return null;
    }

    final coordinates = geometry['coordinates'];
    if (coordinates is! List || coordinates.length < 2) {
      return null;
    }

    final lng = (coordinates[0] as num?)?.toDouble();
    final lat = (coordinates[1] as num?)?.toDouble();
    if (lat == null || lng == null) {
      return null;
    }

    final markerId = properties['id']?.toString() ?? '$lat,$lng';
    return _ReportMarker(
      id: markerId,
      position: LatLng(lat, lng),
      properties: properties,
    );
  }

  _ReportMarker? _parseReportMarker(Map<String, dynamic> report) {
    final lat = (report['latitude'] as num?)?.toDouble();
    final lng = (report['longitude'] as num?)?.toDouble();
    if (lat == null || lng == null) {
      return null;
    }

    final markerId = report['id']?.toString() ?? '$lat,$lng';
    return _ReportMarker(
      id: markerId,
      position: LatLng(lat, lng),
      properties: report,
    );
  }

  Future<void> _fitMapToMarkers(List<_ReportMarker> markers) async {
    if (_mapController == null) {
      return;
    }

    if (markers.isEmpty) {
      await _mapController!.animateCamera(
        CameraUpdate.newCameraPosition(
          const CameraPosition(target: _defaultCenter, zoom: 11),
        ),
      );
      return;
    }

    if (markers.length == 1) {
      final target = markers.first.position;
      _currentCenter = target;
      await _mapController!.animateCamera(
        CameraUpdate.newCameraPosition(
          CameraPosition(target: target, zoom: 15),
        ),
      );
      return;
    }

    var minLat = markers.first.position.latitude;
    var maxLat = markers.first.position.latitude;
    var minLng = markers.first.position.longitude;
    var maxLng = markers.first.position.longitude;

    for (final marker in markers.skip(1)) {
      minLat = marker.position.latitude < minLat ? marker.position.latitude : minLat;
      maxLat = marker.position.latitude > maxLat ? marker.position.latitude : maxLat;
      minLng = marker.position.longitude < minLng ? marker.position.longitude : minLng;
      maxLng = marker.position.longitude > maxLng ? marker.position.longitude : maxLng;
    }

    _currentCenter = LatLng((minLat + maxLat) / 2, (minLng + maxLng) / 2);
    await _mapController!.animateCamera(
      CameraUpdate.newLatLngBounds(
        LatLngBounds(
          southwest: LatLng(minLat, minLng),
          northeast: LatLng(maxLat, maxLng),
        ),
        48,
      ),
    );
  }

  Set<Marker> _buildMarkers() {
    return _markers.map((marker) {
      final severity = marker.properties['severity']?.toString() ?? 'low';
      return Marker(
        markerId: MarkerId(marker.id),
        position: marker.position,
        infoWindow: InfoWindow(
          title: AppConstants.severityLabels[severity] ?? severity,
          snippet: AppConstants.statusLabels[marker.properties['status']] ?? marker.properties['status']?.toString(),
          onTap: () => _showMarkerInfo(marker.properties),
        ),
        icon: _markerHueForSeverity(severity),
        onTap: () => _showMarkerInfo(marker.properties),
      );
    }).toSet();
  }

  BitmapDescriptor _markerHueForSeverity(String severity) {
    switch (severity) {
      case 'high':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed);
      case 'medium':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange);
      default:
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen);
    }
  }

  Future<void> _zoomBy(double delta) async {
    final controller = _mapController;
    if (controller == null) {
      return;
    }

    final currentZoom = await controller.getZoomLevel();
    await controller.animateCamera(CameraUpdate.zoomTo(currentZoom + delta));
  }

  Future<LatLng?> _getCurrentLocation({bool showError = true}) async {
    if (_isLocatingUser) {
      return _userLocation;
    }

    setState(() => _isLocatingUser = true);

    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      final hasPermission =
          permission == LocationPermission.whileInUse ||
          permission == LocationPermission.always;

      if (!mounted) {
        return _userLocation;
      }

      if (!hasPermission) {
        setState(() {
          _hasLocationPermission = false;
          _isLocatingUser = false;
        });

        if (showError) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Location permission is required.')),
          );
        }

        return null;
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
      final userLocation = LatLng(position.latitude, position.longitude);

      if (!mounted) {
        return userLocation;
      }

      setState(() {
        _hasLocationPermission = true;
        _userLocation = userLocation;
        _isLocatingUser = false;
      });

      return userLocation;
    } catch (_) {
      if (!mounted) {
        return null;
      }

      setState(() {
        _hasLocationPermission = false;
        _isLocatingUser = false;
      });

      if (showError) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not get current location.')),
        );
      }

      return null;
    }
  }

  Future<void> _centerOnUser() async {
    final controller = _mapController;
    if (controller == null) {
      return;
    }

    final userLocation = await _getCurrentLocation();
    if (userLocation == null) {
      return;
    }

    await controller.animateCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(target: userLocation, zoom: 16),
      ),
    );
  }

  Future<void> _recenterMap() async {
    final controller = _mapController;
    if (controller == null) {
      return;
    }

    if (_markers.isNotEmpty) {
      await _fitMapToMarkers(_markers);
      return;
    }

    await controller.animateCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(target: _currentCenter, zoom: 11),
      ),
    );
  }

  @override
  void dispose() {
    _mapController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Map'),
        actions: [
          PopupMenuButton<String?>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) {
              setState(() {
                _selectedStatus = value;
              });
              _fetchMarkers();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: null, child: Text('All')),
              ...AppConstants.statusLabels.entries.map(
                (e) => PopupMenuItem(value: e.key, child: Text(e.value)),
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchMarkers,
          ),
        ],
      ),
      body: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: const CameraPosition(target: _defaultCenter, zoom: 11),
            myLocationEnabled: _hasLocationPermission,
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
            mapToolbarEnabled: false,
            compassEnabled: true,
            markers: _buildMarkers(),
            onMapCreated: (controller) {
              _mapController = controller;
              _fitMapToMarkers(_markers);
            },
            onCameraMove: (position) {
              _currentCenter = position.target;
            },
          ),
          if (!_isLoading && _markers.isEmpty)
            const Center(
              child: Card(
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Text('No reports found for the current filter.'),
                ),
              ),
            ),
          if (_isLoading)
            const Positioned(
              top: 16,
              left: 0,
              right: 0,
              child: Center(
                child: Card(
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        SizedBox(width: 8),
                        Text('Loading markers...'),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          Positioned(
            bottom: 16,
            right: 16,
            child: Column(
              children: [
                FloatingActionButton.small(
                  heroTag: 'zoom_in',
                  onPressed: () => _zoomBy(1),
                  child: const Icon(Icons.add),
                ),
                const SizedBox(height: 8),
                FloatingActionButton.small(
                  heroTag: 'zoom_out',
                  onPressed: () => _zoomBy(-1),
                  child: const Icon(Icons.remove),
                ),
                const SizedBox(height: 8),
                FloatingActionButton.small(
                  heroTag: 'center',
                  onPressed: _centerOnUser,
                  child: const Icon(Icons.my_location),
                ),
                const SizedBox(height: 8),
                FloatingActionButton.small(
                  heroTag: 'recenter_reports',
                  onPressed: _recenterMap,
                  child: const Icon(Icons.center_focus_strong),
                ),
              ],
            ),
          ),
          Positioned(
            top: 16,
            left: 16,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Reports: ${_markers.length}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    ...AppConstants.severityLabels.entries.map((e) {
                      return Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 12,
                            height: 12,
                            decoration: BoxDecoration(
                              color: Color(
                                AppConstants.severityColors[e.key] ?? 0xFF9E9E9E,
                              ),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Text(e.value, style: const TextStyle(fontSize: 12)),
                        ],
                      );
                    }),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showMarkerInfo(Map<String, dynamic> props) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Color(
                        AppConstants.statusColors[props['status']] ?? 0xFF9E9E9E,
                      ),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      AppConstants.statusLabels[props['status']] ?? props['status'],
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                   Container(
                     padding: const EdgeInsets.symmetric(
                       horizontal: 12,
                       vertical: 6,
                     ),
                     decoration: BoxDecoration(
                       color: Color(
                         AppConstants.severityColors[props['severity']] ?? 0xFF9E9E9E,
                       ).withValues(alpha: 0.2),
                       borderRadius: BorderRadius.circular(20),
                     ),
                     child: Text(
                       AppConstants.severityLabels[props['severity']] ?? props['severity'],
                       style: TextStyle(
                        color: Color(
                          AppConstants.severityColors[props['severity']] ?? 0xFF9E9E9E,
                        ),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (props['garbage_type'] != null)
                Text('Type: ${props['garbage_type']}'),
              const SizedBox(height: 8),
              Text(
                'Reported: ${_formatDate(props['created_at'])}',
                style: const TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    Navigator.pop(context);
                  },
                  child: const Text('View Details'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year}';
    } catch (_) {
      return dateStr;
    }
  }
}

class _ReportMarker {
  final String id;
  final LatLng position;
  final Map<String, dynamic> properties;

  const _ReportMarker({
    required this.id,
    required this.position,
    required this.properties,
  });
}
