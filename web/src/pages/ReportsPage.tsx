import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Report, ReportDetail, ReportListResponse } from '../types'
import { format } from 'date-fns'
import clsx from 'clsx'
import { Clock, Filter, Check, X, AlertTriangle, User, MapPin } from 'lucide-react'

const STATUS_TRANSITIONS: Record<Report['status'], Report['status'][]> = {
  submitted: ['under_review', 'rejected'],
  under_review: ['scheduled', 'cleaned', 'rejected'],
  scheduled: ['cleaned', 'rejected'],
  cleaned: [],
  rejected: [],
}

const STATUS_COLORS: Record<string, string> = {
  submitted: 'bg-slate-800 text-slate-300 border border-slate-700',
  under_review: 'bg-emerald-950 text-emerald-300 border border-emerald-800',
  scheduled: 'bg-amber-950 text-amber-300 border border-amber-800',
  cleaned: 'bg-lime-950 text-lime-300 border border-lime-800',
  rejected: 'bg-red-950 text-red-300 border border-red-800',
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-400/10',
  medium: 'text-lime-400 bg-lime-400/10',
  high: 'text-amber-400 bg-amber-400/10',
  critical: 'text-red-400 bg-red-400/10',
}

export default function ReportsPage() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
  })
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [selectedReportDetail, setSelectedReportDetail] = useState<ReportDetail | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports', { page, status: filters.status, severity: filters.severity }],
    queryFn: async () => {
      const params: Record<string, string> = {
        page: page.toString(),
        page_size: '20',
      }
      if (filters.status) params.status = filters.status
      if (filters.severity) params.severity = filters.severity

      const response = await api.get<ReportListResponse>('/reports', { params })
      return response.data
    },
    placeholderData: {
      page: 1,
      total_pages: 1,
      total: 0,
      page_size: 20,
      items: [],
    },
    retry: 1,
  })

  const reports = data?.items ?? []
  const pagination = data ?? { page, total_pages: 1, total: 0, page_size: 20, items: [] }

  const updateStatus = async (reportId: string, status: Report['status']) => {
    setStatusError(null)
    setIsUpdatingStatus(true)
    try {
      await api.put(`/reports/${reportId}/status`, { status })
      refetch()
      setSelectedReport(null)
    } catch (error) {
      console.error(error)
      setStatusError('Unable to update report status. Please try again.')
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  const openReviewModal = async (report: Report) => {
    setStatusError(null)
    setDetailError(null)
    setSelectedReport(report)
    setSelectedReportDetail(null)
    setIsLoadingDetail(true)
    try {
      const response = await api.get<ReportDetail>(`/reports/${report.id}`)
      setSelectedReportDetail(response.data)
    } catch (error) {
      console.error(error)
      setDetailError('Unable to load full report details. Showing basic info.')
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const canTransitionTo = (targetStatus: Report['status']) => {
    if (!selectedReport) return false
    return STATUS_TRANSITIONS[selectedReport.status]?.includes(targetStatus) ?? false
  }

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      {isError && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to refresh reports. Showing available data.
        </div>
      )}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Reports</h1>
          <p className="mt-1 text-sm text-slate-500">{pagination.total} reports in total</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 shadow-sm">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={filters.status}
              onChange={(e) => {
                setFilters({ ...filters, status: e.target.value })
                setPage(1)
              }}
              className="bg-transparent text-sm font-medium text-slate-700 outline-none"
            >
              <option value="">All Status</option>
              <option value="submitted">Submitted</option>
              <option value="under_review">Under Review</option>
              <option value="scheduled">Scheduled</option>
              <option value="cleaned">Cleaned</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 shadow-sm">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={filters.severity}
              onChange={(e) => {
                setFilters({ ...filters, severity: e.target.value })
                setPage(1)
              }}
              className="bg-transparent text-sm font-medium text-slate-700 outline-none"
            >
              <option value="">All Severity</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50/50">
              <tr>
                <th className="px-6 py-4 font-medium text-slate-500">ID / Date</th>
                <th className="px-6 py-4 font-medium text-slate-500">Reporter</th>
                <th className="px-6 py-4 font-medium text-slate-500">Type & Severity</th>
                <th className="px-6 py-4 font-medium text-slate-500">Location</th>
                <th className="px-6 py-4 font-medium text-slate-500">Status</th>
                <th className="px-6 py-4 font-medium text-slate-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
                    </div>
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    No reports match the current filters.
                  </td>
                </tr>
              ) : (
                reports.map((report) => (
                  <tr key={report.id} className="transition-colors hover:bg-slate-50/50">
                    <td className="px-6 py-4">
                      <div className="font-mono text-xs text-slate-400">{report.id.slice(0, 8)}</div>
                      <div className="mt-1 font-medium text-slate-900">
                        {format(new Date(report.created_at), 'MMM d, yyyy')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                          <User className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{report.user?.full_name || 'Anonymous Citizen'}</p>
                          <p className="text-xs text-slate-500">{report.user?.phone || report.user?.email || 'No contact info'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-900 capitalize">{report.category?.replace('_', ' ') || '-'}</p>
                      <div className="mt-1">
                        <span className={clsx('inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium capitalize', SEVERITY_COLORS[report.severity])}>
                          {report.severity === 'critical' && <AlertTriangle className="h-3 w-3" />}
                          {report.severity}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex max-w-[200px] items-start gap-2">
                        <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                        <p className="truncate text-slate-600">{report.address || `${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)}`}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={clsx('inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize', STATUS_COLORS[report.status] || 'bg-slate-100 text-slate-700')}>
                        {report.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => openReviewModal(report)}
                        className="inline-flex items-center justify-center rounded-full bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pagination.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/50 px-6 py-4">
            <button
              onClick={() => setPage(page - 1)}
              disabled={pagination.page === 1}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm font-medium text-slate-500">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={pagination.page === pagination.total_pages}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl overflow-hidden rounded-[2rem] bg-white shadow-2xl">
            <div className="border-b border-slate-100 px-6 py-5">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">Report Review</h2>
                <button
                  onClick={() => {
                    setStatusError(null)
                    setDetailError(null)
                    setSelectedReport(null)
                    setSelectedReportDetail(null)
                  }}
                  className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="max-h-[70vh] overflow-y-auto px-6 py-6">
              <div className="mb-8 flex items-center justify-between rounded-2xl bg-slate-50 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                    <User className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Submitted by</p>
                    <p className="font-medium text-slate-900">{selectedReport.user?.full_name || 'Anonymous Citizen'}</p>
                    <p className="text-xs text-slate-500">{selectedReport.user?.phone || selectedReport.user?.email}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-500">Date</p>
                  <p className="font-medium text-slate-900">{format(new Date(selectedReport.created_at), 'PPp')}</p>
                </div>
              </div>

              <div className="mb-6 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Type</p>
                  <p className="font-medium capitalize text-slate-900">{selectedReport.category?.replace('_', ' ') || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status & Severity</p>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={clsx('rounded-full px-2 py-0.5 text-xs font-medium capitalize', STATUS_COLORS[selectedReport.status] || 'bg-slate-100 text-slate-700')}>
                      {selectedReport.status.replace('_', ' ')}
                    </span>
                    <span className={clsx('rounded-full px-2 py-0.5 text-xs font-medium capitalize', SEVERITY_COLORS[selectedReport.severity])}>
                      {selectedReport.severity}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-sm text-slate-500">Location</p>
                <div className="mt-1 flex items-start gap-2">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                  <div>
                    <p className="font-medium text-slate-900">{selectedReport.address || 'Address not available'}</p>
                    <p className="text-sm text-slate-500">{selectedReport.latitude.toFixed(6)}, {selectedReport.longitude.toFixed(6)}</p>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-sm text-slate-500">Description</p>
                <p className="mt-1 text-slate-900">{selectedReport.description || 'No description provided.'}</p>
              </div>

              {detailError && (
                <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {detailError}
                </p>
              )}

              {isLoadingDetail && (
                <div className="mb-6 flex h-64 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
                </div>
              )}

              {((selectedReportDetail?.photos?.length || 0) > 0 || selectedReport.image_url) && (
                <div className="mb-6">
                  <p className="mb-2 text-sm text-slate-500">Image Evidence</p>
                  {(selectedReportDetail?.photos?.length || 0) > 0 ? (
                    <div className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2">
                      {selectedReportDetail!.photos.map((photo, index) => (
                        <img
                          key={photo.id}
                          src={photo.image_url}
                          alt={`Report evidence ${index + 1}`}
                          className="h-64 w-full min-w-full snap-center rounded-2xl object-cover"
                        />
                      ))}
                    </div>
                  ) : (
                    <img
                      src={selectedReport.image_url}
                      alt="Report"
                      className="h-64 w-full rounded-2xl object-cover"
                    />
                  )}
                </div>
              )}
            </div>

            <div className="border-t border-slate-100 bg-slate-50 px-6 py-4">
              <p className="mb-3 text-sm font-medium text-slate-700">Update Status</p>
              {statusError && (
                <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {statusError}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <button
                  disabled={!canTransitionTo('under_review') || isUpdatingStatus}
                  onClick={() => updateStatus(selectedReport.id, 'under_review')}
                  className="flex items-center gap-2 rounded-full bg-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Clock className="h-4 w-4" /> Under Review
                </button>
                <button
                  disabled={!canTransitionTo('scheduled') || isUpdatingStatus}
                  onClick={() => updateStatus(selectedReport.id, 'scheduled')}
                  className="flex items-center gap-2 rounded-full bg-amber-100 px-4 py-2 text-sm font-medium text-amber-700 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Check className="h-4 w-4" /> Schedule
                </button>
                <button
                  disabled={!canTransitionTo('cleaned') || isUpdatingStatus}
                  onClick={() => updateStatus(selectedReport.id, 'cleaned')}
                  className="flex items-center gap-2 rounded-full bg-emerald-100 px-4 py-2 text-sm font-medium text-emerald-700 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Check className="h-4 w-4" /> Mark Cleaned
                </button>
                <button
                  disabled={!canTransitionTo('rejected') || isUpdatingStatus}
                  onClick={() => updateStatus(selectedReport.id, 'rejected')}
                  className="flex items-center gap-2 rounded-full bg-red-100 px-4 py-2 text-sm font-medium text-red-700 transition hover:bg-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <X className="h-4 w-4" /> Rejected
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
