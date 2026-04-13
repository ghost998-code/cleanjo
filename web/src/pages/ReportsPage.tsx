import { useState, useEffect } from 'react'
import api from '../services/api'
import { Report, ReportListResponse } from '../types'
import { format } from 'date-fns'
import clsx from 'clsx'
import { Clock, Filter, Check, X, AlertTriangle } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({
    page: 1,
    total_pages: 1,
    total: 0,
  })
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
  })
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)

  useEffect(() => {
    fetchReports()
  }, [pagination.page, filters])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {
        page: pagination.page.toString(),
        page_size: '20',
      }
      if (filters.status) params.status = filters.status
      if (filters.severity) params.severity = filters.severity

      const response = await api.get<ReportListResponse>('/reports', { params })
      setReports(response.data.items)
      setPagination({
        page: response.data.page,
        total_pages: response.data.total_pages,
        total: response.data.total,
      })
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (reportId: string, status: string) => {
    try {
      await api.patch(`/reports/${reportId}`, { status })
      fetchReports()
      setSelectedReport(null)
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Reports</h1>
          <p className="text-gray-500">{pagination.total} total reports</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-600">Filters:</span>
          </div>
          <select
            value={filters.status}
            onChange={(e) => {
              setFilters({ ...filters, status: e.target.value })
              setPagination({ ...pagination, page: 1 })
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={filters.severity}
            onChange={(e) => {
              setFilters({ ...filters, severity: e.target.value })
              setPagination({ ...pagination, page: 1 })
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Severity</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    </div>
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No reports found
                  </td>
                </tr>
              ) : (
                reports.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {report.id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                      {report.garbage_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={clsx(
                          'px-2 py-1 rounded-full text-xs font-medium',
                          STATUS_COLORS[report.status]
                        )}
                      >
                        {report.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={clsx(
                          'px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 w-fit',
                          SEVERITY_COLORS[report.severity]
                        )}
                      >
                        <AlertTriangle className="w-3 h-3" />
                        {report.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 max-w-xs truncate">
                      {report.address || `${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {format(new Date(report.created_at), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pagination.total_pages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <button
              onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
              disabled={pagination.page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
              disabled={pagination.page === pagination.total_pages}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-800">Report Details</h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex gap-2">
                <span
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm font-medium',
                    STATUS_COLORS[selectedReport.status]
                  )}
                >
                  {selectedReport.status.replace('_', ' ')}
                </span>
                <span
                  className={clsx(
                    'px-3 py-1 rounded-full text-sm font-medium',
                    SEVERITY_COLORS[selectedReport.severity]
                  )}
                >
                  {selectedReport.severity}
                </span>
              </div>

              <div>
                <p className="text-sm text-gray-500">Type</p>
                <p className="font-medium">{selectedReport.garbage_type || '-'}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Location</p>
                <p className="font-medium">{selectedReport.address || '-'}</p>
                <p className="text-sm text-gray-500">
                  {selectedReport.latitude.toFixed(6)}, {selectedReport.longitude.toFixed(6)}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Description</p>
                <p>{selectedReport.description || '-'}</p>
              </div>

              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p>{format(new Date(selectedReport.created_at), 'PPpp')}</p>
              </div>

              {selectedReport.image_url && (
                <div>
                  <p className="text-sm text-gray-500 mb-2">Image</p>
                  <img
                    src={selectedReport.image_url}
                    alt="Report"
                    className="w-full h-48 object-cover rounded-lg"
                  />
                </div>
              )}

              <div className="pt-4 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-3">Update Status</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => updateStatus(selectedReport.id, 'in_progress')}
                    className="flex items-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm hover:bg-blue-200"
                  >
                    <Clock className="w-4 h-4" /> In Progress
                  </button>
                  <button
                    onClick={() => updateStatus(selectedReport.id, 'resolved')}
                    className="flex items-center gap-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm hover:bg-green-200"
                  >
                    <Check className="w-4 h-4" /> Resolved
                  </button>
                  <button
                    onClick={() => updateStatus(selectedReport.id, 'rejected')}
                    className="flex items-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    <X className="w-4 h-4" /> Rejected
                  </button>
                </div>
              </div>
            </div>
            <div className="p-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedReport(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
