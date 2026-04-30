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
    'submitted': 'Submitted',
    'under_review': 'Under Review',
    'scheduled': 'Scheduled',
    'cleaned': 'Cleaned',
    'rejected': 'Rejected',
  };

  static const Map<String, int> severityColors = {
    'low': 0xFF4CAF50,
    'medium': 0xFFFFC107,
    'high': 0xFFFF9800,
    'critical': 0xFFF44336,
  };

  static const Map<String, int> statusColors = {
    'submitted': 0xFF94A3B8,
    'under_review': 0xFF2196F3,
    'scheduled': 0xFFFF9800,
    'cleaned': 0xFF4CAF50,
    'rejected': 0xFFF44336,
  };
}
