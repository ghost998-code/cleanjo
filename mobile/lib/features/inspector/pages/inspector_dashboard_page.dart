import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../core/auth/auth_bloc.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../../core/di/injection.dart';

class InspectorDashboardPage extends StatefulWidget {
  const InspectorDashboardPage({super.key});

  @override
  State<InspectorDashboardPage> createState() => _InspectorDashboardPageState();
}

class _InspectorDashboardPageState extends State<InspectorDashboardPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _assignedReports = [];
  List<dynamic> _allReports = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchReports();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchReports() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = getIt<ApiClient>();
      
      final assignedResponse = await apiClient.get('/reports', queryParameters: {
        'page_size': 50,
      });
      final allResponse = await apiClient.get('/reports', queryParameters: {
        'status': 'pending',
        'page_size': 50,
      });
      
      setState(() {
        _assignedReports = assignedResponse.data['items'] ?? [];
        _allReports = allResponse.data['items'] ?? [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _updateReportStatus(
    String reportId,
    String newStatus, {
    String? notes,
  }) async {
    try {
      final apiClient = getIt<ApiClient>();
      await apiClient.patch('/reports/$reportId', data: {
        'status': newStatus,
        'notes': notes,
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Report marked as $newStatus'),
            backgroundColor: Colors.green,
          ),
        );
        _fetchReports();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to update report'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspector Dashboard'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: 'Assigned (${_assignedReports.length})'),
            Tab(text: 'Unassigned (${_allReports.length})'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchReports,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildReportList(_assignedReports, showActions: true),
                _buildReportList(_allReports, showActions: false),
              ],
            ),
    );
  }

  Widget _buildReportList(List<dynamic> reports, {required bool showActions}) {
    if (reports.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'No reports',
              style: TextStyle(fontSize: 18, color: Colors.grey[600]),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchReports,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: reports.length,
        itemBuilder: (context, index) {
          final report = reports[index];
          return _InspectorReportCard(
            report: report,
            showActions: showActions,
            onStatusUpdate: (status, notes) => _updateReportStatus(
              report['id'],
              status,
              notes: notes,
            ),
            onAssign: () => _assignReport(report['id']),
          );
        },
      ),
    );
  }

  Future<void> _assignReport(String reportId) async {
    final authState = context.read<AuthBloc>().state;
    if (authState is! AuthAuthenticated) return;

    try {
      final apiClient = getIt<ApiClient>();
      await apiClient.patch('/reports/$reportId', data: {
        'assigned_to': authState.user.id,
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Report assigned to you'),
            backgroundColor: Colors.green,
          ),
        );
        _fetchReports();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to assign report'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}

class _InspectorReportCard extends StatelessWidget {
  final Map<String, dynamic> report;
  final bool showActions;
  final Function(String status, String? notes) onStatusUpdate;
  final VoidCallback onAssign;

  const _InspectorReportCard({
    required this.report,
    required this.showActions,
    required this.onStatusUpdate,
    required this.onAssign,
  });

  @override
  Widget build(BuildContext context) {
    final isAssigned = report['assigned_to'] != null;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: Color(
                      AppConstants.severityColors[report['severity']] ?? 0xFF9E9E9E,
                    ),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    report['garbage_type'] ?? 'Unknown type',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: Color(
                      AppConstants.statusColors[report['status']] ?? 0xFF9E9E9E,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    AppConstants.statusLabels[report['status']] ?? report['status'],
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (report['address'] != null && report['address'].isNotEmpty)
              Row(
                children: [
                  const Icon(Icons.location_on, size: 16, color: Colors.grey),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      report['address'],
                      style: const TextStyle(fontSize: 14, color: Colors.grey),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.access_time, size: 16, color: Colors.grey),
                const SizedBox(width: 4),
                Text(
                  _formatDate(report['created_at']),
                  style: const TextStyle(fontSize: 14, color: Colors.grey),
                ),
                if (isAssigned) ...[
                  const SizedBox(width: 12),
                  const Icon(Icons.person, size: 16, color: Colors.blue),
                  const SizedBox(width: 4),
                  const Text(
                    'Assigned',
                    style: TextStyle(fontSize: 14, color: Colors.blue),
                  ),
                ],
              ],
            ),
            if (showActions && report['status'] == 'pending') ...[
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  TextButton.icon(
                    onPressed: () => _showUpdateDialog(context, 'in_progress'),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Start'),
                  ),
                  TextButton.icon(
                    onPressed: () => _showUpdateDialog(context, 'resolved'),
                    icon: const Icon(Icons.check, color: Colors.green),
                    label: const Text('Resolve', style: TextStyle(color: Colors.green)),
                  ),
                  TextButton.icon(
                    onPressed: () => _showUpdateDialog(context, 'rejected'),
                    icon: const Icon(Icons.close, color: Colors.red),
                    label: const Text('Reject', style: TextStyle(color: Colors.red)),
                  ),
                ],
              ),
            ],
            if (!showActions && !isAssigned) ...[
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: onAssign,
                  icon: const Icon(Icons.assignment_ind),
                  label: const Text('Assign to Me'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showUpdateDialog(BuildContext context, String status) {
    final notesController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Update to ${AppConstants.statusLabels[status]}'),
        content: TextField(
          controller: notesController,
          decoration: const InputDecoration(
            labelText: 'Notes (optional)',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              onStatusUpdate(status, notesController.text.isNotEmpty ? notesController.text : null);
            },
            child: const Text('Update'),
          ),
        ],
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
}
