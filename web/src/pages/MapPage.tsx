import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Layers3, MapPinned } from 'lucide-react'

import ReportsMap from '../components/ReportsMap'
import api from '../services/api'
import { ReportListResponse } from '../types'

export default function MapPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const normalizedStatusFilter = statusFilter || undefined

  const { data: reports = [], isFetching: loading, isError } = useQuery({
    queryKey: normalizedStatusFilter
      ? ['map-reports', { page_size: 100, status: normalizedStatusFilter }]
      : ['map-reports', { page_size: 100 }],
    queryFn: async () => {
      const params: Record<string, string> = { page_size: '100' }
      if (normalizedStatusFilter) {
        params.status = normalizedStatusFilter
      }
      const response = await api.get<ReportListResponse>('/reports', { params })
      return response.data.items || []
    },
    placeholderData: [],
    retry: 1,
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-emerald-600/70">Operations map</p>
          <h1 className="mt-2 text-2xl font-bold text-gray-800">All reports pinned by location</h1>
          <p className="text-gray-500">{reports.length} visible reports</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-full border border-emerald-100 bg-white px-4 py-2 text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Status</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under Review</option>
            <option value="scheduled">Scheduled</option>
            <option value="cleaned">Cleaned</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="overflow-hidden rounded-[2rem] bg-white shadow-sm">
          <div className="h-[calc(100vh-280px)] min-h-[560px] bg-slate-950">
            {isError ? (
              <div className="flex h-full items-center justify-center px-6 text-center text-red-300">
                Failed to load map reports. Please refresh and verify API connectivity.
              </div>
            ) : (
              <div className="relative h-full w-full">
                {loading && (
                  <div className="absolute right-4 top-4 z-10 rounded-full bg-slate-900/70 px-3 py-1 text-xs text-white">
                    Syncing...
                  </div>
                )}
                <ReportsMap reports={reports} />
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-4">
          <div className="rounded-[2rem] bg-[linear-gradient(135deg,#052e16_0%,#0f172a_100%)] p-5 text-white shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-emerald-400/15 p-3 text-emerald-200">
                <MapPinned className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-emerald-200/70">Map state</p>
                <h2 className="mt-1 text-xl font-semibold">Live pins</h2>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-emerald-50/72">
              This view keeps every report visible in its recorded location so admins can monitor spread, density, and response coverage.
            </p>
          </div>

          <div className="rounded-[2rem] bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
                <Layers3 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Reports Sidebar</h3>
                <p className="text-sm text-slate-500">List of visible reports.</p>
              </div>
            </div>
            <div className="mt-4 flex flex-col gap-3 max-h-[300px] overflow-y-auto pr-2">
              {reports.map((report) => (
                <div key={report.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase text-slate-500">{report.category?.replace('_', ' ')}</span>
                    <span className="text-xs font-medium text-slate-400">{new Date(report.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-700">{report.address || 'No address'}</p>
                </div>
              ))}
              {reports.length === 0 && (
                <p className="text-sm text-slate-500">No reports found.</p>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
