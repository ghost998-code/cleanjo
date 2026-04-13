export interface User {
  id: string
  email: string
  full_name?: string
  role: 'citizen' | 'inspector' | 'admin'
  phone?: string
  created_at: string
}

export interface Report {
  id: string
  user_id: string
  latitude: number
  longitude: number
  address?: string
  garbage_type?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  image_url?: string
  description?: string
  status: 'pending' | 'in_progress' | 'resolved' | 'rejected'
  assigned_to?: string
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
    garbage_type?: string
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
