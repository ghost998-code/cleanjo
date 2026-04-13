class AppConstants {
  static const String appName = 'Garbage Detection';
  
  static const List<String> garbageTypes = [
    'plastic',
    'paper',
    'glass',
    'metal',
    'organic',
    'electronic',
    'hazardous',
    'construction',
    'mixed',
    'other',
  ];

  static const Map<String, String> severityLabels = {
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
    'critical': 'Critical',
  };

  static const Map<String, String> statusLabels = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'resolved': 'Resolved',
    'rejected': 'Rejected',
  };

  static const Map<String, int> severityColors = {
    'low': 0xFF4CAF50,
    'medium': 0xFFFFC107,
    'high': 0xFFFF9800,
    'critical': 0xFFF44336,
  };

  static const Map<String, int> statusColors = {
    'pending': 0xFF9E9E9E,
    'in_progress': 0xFF2196F3,
    'resolved': 0xFF4CAF50,
    'rejected': 0xFFF44336,
  };
}
