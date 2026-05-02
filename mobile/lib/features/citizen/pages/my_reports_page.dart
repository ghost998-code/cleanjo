import 'package:flutter/material.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/offline/sync_service.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/network/api_client.dart';
import '../../../core/di/injection.dart';

class MyReportsPage extends StatefulWidget {
  const MyReportsPage({super.key});

  @override
  State<MyReportsPage> createState() => _MyReportsPageState();
}

class _MyReportsPageState extends State<MyReportsPage>
    with WidgetsBindingObserver {
  List<dynamic> _reports = [];
  bool _isLoading = true;
  String? _selectedStatus;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _fetchReports();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _fetchReports();
    }
  }

  Future<void> _fetchReports() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = getIt<ApiClient>();
      final syncService = getIt<SyncService>();
      await syncService.syncPendingReports();
      final queryParams = <String, dynamic>{};
      if (_selectedStatus != null) {
        queryParams['status'] = _selectedStatus;
      }

      final response =
          await apiClient.get(ApiEndpoints.reports + '/me', queryParameters: queryParams);
      
      final pendingReports = _buildPendingReports(syncService);
      setState(() {
        _reports = [
          ...pendingReports,
          ...(response.data['items'] as List? ?? const []),
        ];
        _isLoading = false;
      });
    } catch (e) {
      debugPrint('Error fetching reports: $e');
      setState(() {
        _reports = _buildPendingReports(getIt<SyncService>());
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to load reports. Please try again.')),
        );
      }
    }
  }

  List<Map<String, dynamic>> _buildPendingReports(SyncService syncService) {
    if (_selectedStatus != null &&
        _selectedStatus != 'pending_sync' &&
        _selectedStatus != 'failed_sync') {
      return const [];
    }

    return syncService
        .getPendingReports()
        .map((report) {
          final localStatus =
              report.syncStatus == 'failed' ? 'failed_sync' : 'pending_sync';
          if (_selectedStatus != null && _selectedStatus != localStatus) {
            return null;
          }

          return <String, dynamic>{
            'id': report.localId,
            'is_local_only': true,
            'status': localStatus,
            'severity': report.draft.severity,
            'garbage_type': report.draft.category,
            'address': report.draft.address ?? '',
            'description': report.draft.description,
            'created_at': report.createdAt.toIso8601String(),
            'sync_error': report.lastError,
            'photos': report.draft.photos
                .map(
                  (photo) => <String, dynamic>{
                    'predicted_category': photo.inference?.predictedCategory,
                    'prediction_confidence':
                        photo.inference?.predictionConfidence,
                    'predicted_severity': photo.inference?.predictedSeverity,
                    'model_name': photo.inference?.modelName,
                    'model_version': photo.inference?.modelVersion,
                    'inference_source': photo.inference?.inferenceSource,
                    'top_predictions': photo.inference?.topPredictions
                            .map((prediction) => prediction.toJson())
                            .toList() ??
                        const [],
                  },
                )
                .toList(),
            'inference_summary_category':
                report.draft.inferenceSummary?.summaryCategory,
            'inference_summary_confidence':
                report.draft.inferenceSummary?.summaryConfidence,
            'inference_summary_strategy':
                report.draft.inferenceSummary?.summaryStrategy,
          };
        })
        .whereType<Map<String, dynamic>>()
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Reports'),
        actions: [
          PopupMenuButton<String?>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) {
              setState(() {
                _selectedStatus = value;
              });
              _fetchReports();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: null, child: Text('All')),
              ...AppConstants.statusLabels.entries.map(
                (e) => PopupMenuItem(value: e.key, child: Text(e.value)),
              ),
            ],
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _reports.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.inbox_outlined,
                        size: 64,
                        color: Colors.grey[400],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'No reports yet',
                        style: TextStyle(
                          fontSize: 18,
                          color: Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: () async {
                          final created = await Navigator.of(context)
                              .pushNamed('/create-report');
                          if (created == true) {
                            _fetchReports();
                          }
                        },
                        icon: const Icon(Icons.add),
                        label: const Text('Create Report'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _fetchReports,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _reports.length,
                    itemBuilder: (context, index) {
                      final report = _reports[index];
                      return _ReportCard(
                        report: report,
                        onTap: () => _showReportDetails(report),
                      );
                    },
                  ),
                ),
    );
  }

  Future<void> _showReportDetails(Map<String, dynamic> report) async {
    Map<String, dynamic> detail = report;
    if (report['is_local_only'] == true) {
      if (!mounted) {
        return;
      }
      _showReportDetailsSheet(detail);
      return;
    }

    final reportId = report['id']?.toString();
    if (reportId != null) {
      try {
        final response =
            await getIt<ApiClient>().get('${ApiEndpoints.reports}/$reportId');
        if (response.data is Map<String, dynamic>) {
          detail = response.data as Map<String, dynamic>;
        }
      } catch (_) {}
    }

    if (!mounted) {
      return;
    }

    _showReportDetailsSheet(detail);
  }

  void _showReportDetailsSheet(Map<String, dynamic> detail) {
    final photos = (detail['photos'] as List?) ?? const [];

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Color(
                        AppConstants.statusColors[detail['status']] ??
                            0xFF9E9E9E,
                      ),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      AppConstants.statusLabels[detail['status']] ??
                          detail['status'],
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
                        AppConstants.severityColors[detail['severity']] ??
                            0xFF9E9E9E,
                      ).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      AppConstants.severityLabels[detail['severity']] ??
                          detail['severity'],
                      style: TextStyle(
                        color: Color(
                          AppConstants.severityColors[detail['severity']] ??
                              0xFF9E9E9E,
                        ),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (detail['garbage_type'] != null) ...[
                Text(
                  'Type: ${detail['garbage_type']}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 8),
              ],
              if (detail['address'] != null &&
                  detail['address'].isNotEmpty) ...[
                Row(
                  children: [
                    const Icon(Icons.location_on, size: 16, color: Colors.grey),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        detail['address'],
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
              ],
              Row(
                children: [
                  const Icon(Icons.access_time, size: 16, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    _formatDate(detail['created_at']),
                    style: const TextStyle(color: Colors.grey),
                  ),
                ],
              ),
              if (detail['inference_summary_category'] != null) ...[
                const SizedBox(height: 16),
                Card(
                  color: const Color(0xFFF0FDF4),
                  child: ListTile(
                    leading: const Icon(Icons.memory, color: Color(0xFF166534)),
                    title: Text(
                        'Device summary: ${detail['inference_summary_category']}'),
                    subtitle: Text(
                      '${_formatConfidence(detail['inference_summary_confidence'])} confidence • ${detail['inference_summary_strategy'] ?? 'mobile'}',
                    ),
                  ),
                ),
              ],
              if (detail['description'] != null &&
                  detail['description'].isNotEmpty) ...[
                const SizedBox(height: 16),
                const Divider(),
                const SizedBox(height: 16),
                Text(
                  detail['description'],
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
              if (detail['sync_error'] != null &&
                  detail['sync_error'].toString().isNotEmpty) ...[
                const SizedBox(height: 16),
                Card(
                  color: const Color(0xFFFEF2F2),
                  child: ListTile(
                    leading: const Icon(Icons.sync_problem,
                        color: Color(0xFFB91C1C)),
                    title: const Text('Sync failed'),
                    subtitle: Text(detail['sync_error'].toString()),
                  ),
                ),
              ],
              if (photos.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Divider(),
                const SizedBox(height: 16),
                const Text(
                  'Per-photo device inference',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                ...photos.whereType<Map>().map((photo) {
                  final topPredictions =
                      (photo['top_predictions'] as List?) ?? const [];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${photo['predicted_category']} • ${_formatConfidence(photo['prediction_confidence'])}',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          if (photo['predicted_severity'] != null) ...[
                            const SizedBox(height: 4),
                            Text('Severity: ${photo['predicted_severity']}'),
                          ],
                          const SizedBox(height: 4),
                          Text(
                            'Source: ${photo['inference_source']} • Model ${photo['model_name']} ${photo['model_version']}',
                            style: const TextStyle(color: Colors.grey),
                          ),
                          if (topPredictions.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: topPredictions
                                  .whereType<Map>()
                                  .map((prediction) {
                                return Chip(
                                  label: Text(
                                    '${prediction['label']} ${_formatConfidence(prediction['confidence'])}',
                                  ),
                                );
                              }).toList(),
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return dateStr;
    }
  }

  String _formatConfidence(dynamic value) {
    final numericValue = (value as num?)?.toDouble();
    if (numericValue == null) {
      return '--';
    }
    return '${(numericValue * 100).toStringAsFixed(0)}%';
  }
}

class _ReportCard extends StatelessWidget {
  final Map<String, dynamic> report;
  final VoidCallback onTap;

  const _ReportCard({
    required this.report,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 8,
                height: 60,
                decoration: BoxDecoration(
                  color: Color(
                    AppConstants.severityColors[report['severity']] ??
                        0xFF9E9E9E,
                  ),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: Color(
                              AppConstants.statusColors[report['status']] ??
                                  0xFF9E9E9E,
                            ),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            AppConstants.statusLabels[report['status']] ??
                                report['status'],
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        if (report['garbage_type'] != null)
                          Text(
                            report['garbage_type'],
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    if (report['address'] != null &&
                        report['address'].isNotEmpty)
                      Text(
                        report['address'],
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w500),
                      ),
                    const SizedBox(height: 4),
                    Text(
                      _formatDate(report['created_at']),
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[500],
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
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
