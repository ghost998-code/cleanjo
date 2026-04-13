import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import api from '../services/api'
import { GeoJSONResponse } from '../types'
import 'leaflet/dist/leaflet.css'

const SEVERITY_COLORS: Record<string, string> = {
  low: '#22C55E',
  medium: '#EAB308',
  high: '#F97316',
  critical: '#EF4444',
}

function createIcon(color: string) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

function HeatmapLayer({ points }: { points: Array<{ lat: number; lng: number; weight: number }> }) {
  const map = useMap()

  useEffect(() => {
    const heatmapData = points.map((p) => [p.lat, p.lng, p.weight])
    
    // @ts-ignore
    if (typeof L.heatLayer !== 'undefined') {
      // @ts-ignore
      const heatLayer = L.heatLayer(heatmapData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
        gradient: {
          0.2: '#22C55E',
          0.4: '#EAB308',
          0.6: '#F97316',
          0.8: '#EF4444',
          1.0: '#DC2626',
        },
      }).addTo(map)

      return () => {
        map.removeLayer(heatLayer)
      }
    }
  }, [points, map])

  return null
}

export default function MapPage() {
  const [features, setFeatures] = useState<GeoJSONResponse['features']>([])
  const [loading, setLoading] = useState(true)
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    fetchMarkers()
  }, [statusFilter])

  const fetchMarkers = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter

      const response = await api.get<GeoJSONResponse>('/reports/map', { params })
      setFeatures(response.data.features || [])
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const heatmapPoints = features.map((f) => ({
    lat: f.geometry.coordinates[1],
    lng: f.geometry.coordinates[0],
    weight: f.properties.severity === 'critical' ? 5 : 
            f.properties.severity === 'high' ? 3 : 
            f.properties.severity === 'medium' ? 2 : 1,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Map View</h1>
          <p className="text-gray-500">{features.length} markers</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              showHeatmap
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {showHeatmap ? 'Show Markers' : 'Show Heatmap'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="h-[calc(100vh-280px)] min-h-[500px]">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <MapContainer
              center={[0, 0]}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              {showHeatmap ? (
                <HeatmapLayer points={heatmapPoints} />
              ) : (
                features.map((feature) => {
                  const color = SEVERITY_COLORS[feature.properties.severity] || '#9CA3AF'
                  return (
                    <Marker
                      key={feature.properties.id}
                      position={[
                        feature.geometry.coordinates[1],
                        feature.geometry.coordinates[0],
                      ]}
                      icon={createIcon(color)}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-bold">{feature.properties.garbage_type || 'Unknown'}</p>
                          <p>Status: {feature.properties.status}</p>
                          <p>Severity: {feature.properties.severity}</p>
                        </div>
                      </Popup>
                    </Marker>
                  )
                })
              )}
            </MapContainer>
          )}
        </div>
      </div>

      <div className="flex items-center gap-6">
        <span className="text-sm font-medium text-gray-600">Legend:</span>
        {Object.entries(SEVERITY_COLORS).map(([severity, color]) => (
          <div key={severity} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: color }}
            ></div>
            <span className="text-sm text-gray-600 capitalize">{severity}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
