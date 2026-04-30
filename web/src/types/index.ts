export interface User {
  id: string
  email: string
  full_name?: string
  role: 'citizen' | 'inspector' | 'admin'
  phone?: string
  created_at: string
}

export interface AdminPreferences {
  notify_on_critical: boolean
  compact_report_cards: boolean
  auto_refresh_map: boolean
}

export interface AdminSettingsResponse {
  full_name?: string
  email: string
  phone?: string
  role: 'admin' | 'inspector' | 'citizen'
  preferences: AdminPreferences
}

export interface Report {
  id: string
  user_id: string
  latitude: number
  longitude: number
  address?: string
  locality?: string
  category: 'household' | 'construction' | 'green' | 'hazardous' | 'electronic' | 'bulky' | 'mixed' | 'other'
  severity: 'low' | 'medium' | 'high' | 'critical'
  image_url?: string
  video_url?: string
  description?: string
  gps_accuracy?: number
  reported_at?: string
  terrain: 'street' | 'sidewalk' | 'open_lot' | 'waterway' | 'residential' | 'industrial' | 'other'
  reachability: 'easy' | 'moderate' | 'hard' | 'requires_special_equipment'
  density: 'sparse' | 'moderate' | 'dense' | 'illegal_dump'
  amount_estimate: '1_bag' | '2_5_bags' | '6_15_bags' | 'truckload'
  status: 'submitted' | 'under_review' | 'scheduled' | 'cleaned' | 'rejected'
  assigned_to?: string
  admin_notes?: string
  created_at: string
  updated_at: string
}

export interface ReportListResponse {
  items: Report[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface GeoJSONFeature {
  type: 'Feature'
  geometry: {
    type: 'Point'
    coordinates: [number, number]
  }
  properties: {
    id: string
    status: string
    severity: string
    category?: string
    created_at: string
  }
}

export interface GeoJSONResponse {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
}

export interface AnalyticsSummary {
  period_days: number
  total_reports: number
  by_status: Record<string, number>
  by_severity: Record<string, number>
  daily_trend: Array<{ date: string; count: number }>
}

export interface HeatmapPoint {
  lat: number
  lng: number
  weight: number
}
