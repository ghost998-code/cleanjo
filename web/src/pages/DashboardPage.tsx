import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle,
  Clock,
  FileText,
  MapPinned,
  TrendingUp,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import ReportsMap from '../components/ReportsMap'
import api from '../services/api'
import { AnalyticsSummary, ReportListResponse } from '../types'

const STATUS_COLORS: Record<string, string> = {
  submitted: '#94A3B8',
  under_review: '#34D399',
  scheduled: '#D7FF64',
  cleaned: '#22C55E',
  rejected: '#EF4444',
}

const SEVERITY_COLORS: Record<string, string> = {
  low: '#22C55E',
  medium: '#D7FF64',
  high: '#F59E0B',
  critical: '#EF4444',
}

const EMPTY_ANALYTICS: AnalyticsSummary = {
  period_days: 30,
  total_reports: 0,
  by_status: {},
  by_severity: {},
  daily_trend: [],
}

export default function DashboardPage() {
  const {
    data: analytics,
    isFetching: fetchingAnalytics,
    isError: isAnalyticsError,
  } = useQuery({
    queryKey: ['analytics-summary', { days: 30 }],
    queryFn: async () => {
      const response = await api.get<AnalyticsSummary>('/analytics/summary', { params: { days: 30 } })
      return response.data
    },
    placeholderData: EMPTY_ANALYTICS,
    retry: 1,
  })

  const {
    data: reports = [],
    isFetching: fetchingReports,
    isError: isReportsError,
  } = useQuery({
    queryKey: ['map-reports', { page_size: 1000 }],
    queryFn: async () => {
      const response = await api.get<ReportListResponse>('/reports', { params: { page_size: '1000' } })
      return response.data.items || []
    },
    placeholderData: [],
    retry: 1,
  })

  const loading = fetchingAnalytics || fetchingReports
  const hasError = isAnalyticsError || isReportsError

  const total = analytics?.total_reports || 0
  const statusData = analytics?.by_status
    ? Object.entries(analytics.by_status).map(([name, value]) => ({
        name,
        value,
        color: STATUS_COLORS[name] || '#9CA3AF',
      }))
    : []

  const severityData = analytics?.by_severity
    ? Object.entries(analytics.by_severity).map(([name, value]) => ({
        name,
        value,
        color: SEVERITY_COLORS[name] || '#9CA3AF',
      }))
    : []

  const criticalReports = analytics?.by_severity?.critical || 0
  const reviewedReports =
    (analytics?.by_status?.under_review || 0) +
    (analytics?.by_status?.scheduled || 0)

  return (
    <div className="space-y-8 text-slate-900">
      {(loading || hasError) && (
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          {hasError
            ? 'Some dashboard data failed to load. Showing last known values.'
            : 'Syncing dashboard data...'}
        </div>
      )}
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="overflow-hidden rounded-[2rem] bg-[linear-gradient(135deg,#03120a_0%,#0f1f17_60%,#163126_100%)] p-6 text-white shadow-[0_30px_80px_rgba(15,23,42,0.18)] sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl">
              <p className="text-sm font-medium uppercase tracking-[0.28em] text-emerald-200/70">
                CleanJO Network
              </p>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
                Command every cleanup decision from a live, map-first admin dashboard.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-emerald-50/72 sm:text-base">
                Reports are pinned by location, trends are surfaced instantly, and critical cases stay visible without leaving the operations view.
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/8 px-5 py-4 text-right backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-emerald-100/60">Pinned reports</p>
              <p className="mt-2 text-4xl font-semibold text-emerald-200">{reports.length}</p>
            </div>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <HeroMetric label="Active review queue" value={reviewedReports} tone="emerald" />
            <HeroMetric label="Critical signals" value={criticalReports} tone="amber" />
            <HeroMetric label="Resolved cases" value={analytics?.by_status?.cleaned || 0} tone="lime" />
          </div>
        </section>

        <section className="rounded-[2rem] border border-emerald-100 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-emerald-600/70">Field pulse</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">What needs attention</h2>
            </div>
            <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <InsightRow label="New submissions" value={analytics?.by_status?.submitted || 0} helper="Fresh cases waiting for triage" />
            <InsightRow label="Under review" value={analytics?.by_status?.under_review || 0} helper="Reports currently being inspected" />
            <InsightRow label="Scheduled" value={analytics?.by_status?.scheduled || 0} helper="Assigned to cleanup planning" />
            <InsightRow label="Cleaned" value={analytics?.by_status?.cleaned || 0} helper="Finished reports in the selected period" />
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total Reports" value={total} icon={FileText} color="emerald" />
        <StatCard title="Submitted" value={analytics?.by_status?.submitted || 0} icon={Clock} color="slate" />
        <StatCard title="Under Review" value={analytics?.by_status?.under_review || 0} icon={TrendingUp} color="amber" />
        <StatCard title="Cleaned" value={analytics?.by_status?.cleaned || 0} icon={CheckCircle} color="lime" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="overflow-hidden rounded-[2rem] border border-slate-900/5 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-emerald-600/70">Live report map</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">Pinned incidents across the network</h2>
            </div>
            <a
              href="/admin/map"
              className="inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100"
            >
              Full map
              <ArrowUpRight className="h-4 w-4" />
            </a>
          </div>
          <div className="h-[460px] bg-slate-950">
            <ReportsMap reports={reports} />
          </div>
        </section>

        <div className="grid gap-6">
          <div className="rounded-[2rem] bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
                <MapPinned className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Coverage snapshot</h2>
                <p className="text-sm text-slate-500">Reports by status in the selected period</p>
              </div>
            </div>
            <div className="h-64">
              {statusData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={82}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`status-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-400">
                  No data available
                </div>
              )}
            </div>
          </div>

          <div className="rounded-[2rem] bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Reports by Severity</h2>
            <div className="h-64">
              {severityData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={82}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                    >
                      {severityData.map((entry, index) => (
                        <Cell key={`severity-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-gray-400">
                  No data available
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">Daily Trend (Last 30 Days)</h2>
        <div className="h-64">
          {analytics?.daily_trend && analytics.daily_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.daily_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })
                  }
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Bar dataKey="count" fill="#22C55E" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              No data available
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function HeroMetric({ label, value, tone }: { label: string; value: number; tone: 'emerald' | 'amber' | 'lime' }) {
  const toneClasses: Record<string, string> = {
    emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
    amber: 'border-amber-300/20 bg-amber-300/10 text-amber-100',
    lime: 'border-lime-300/20 bg-lime-300/10 text-lime-100',
  }

  return (
    <div className={`rounded-[1.75rem] border p-5 backdrop-blur ${toneClasses[tone]}`}>
      <p className="text-sm uppercase tracking-[0.2em] text-white/60">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    </div>
  )
}

function InsightRow({ label, value, helper }: { label: string; value: number; helper: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
      <div>
        <p className="font-medium text-slate-900">{label}</p>
        <p className="text-sm text-slate-500">{helper}</p>
      </div>
      <p className="text-2xl font-semibold text-emerald-700">{value}</p>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: number
  icon: any
  color: string
}) {
  const colorClasses: Record<string, string> = {
    emerald: 'bg-emerald-50 text-emerald-600',
    slate: 'bg-slate-100 text-slate-700',
    amber: 'bg-amber-50 text-amber-600',
    lime: 'bg-lime-50 text-lime-600',
  }

  return (
    <div className="rounded-[1.75rem] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className={`rounded-lg p-3 ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-800">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{title}</p>
    </div>
  )
}
