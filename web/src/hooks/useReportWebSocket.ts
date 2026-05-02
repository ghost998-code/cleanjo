import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Report, ReportListResponse } from '../types'

type ReportEvent = {
  type: 'CREATED' | 'UPDATED' | 'DELETED'
  data: Report
}

type ReportsQueryKey = [
  'reports',
  {
    page: number
    status: string
    severity: string
  },
]

type MapReportsQueryKey = [
  'map-reports',
  {
    page_size: number
    status: string
  },
]

const reportsWebSocketUrl = import.meta.env.VITE_REPORTS_WS_URL ?? 'ws://localhost:8001'

function isNewerReport(incoming: Report, current: Report) {
  return new Date(incoming.updated_at).getTime() > new Date(current.updated_at).getTime()
}

function reportMatchesFilters(report: Report, filters: ReportsQueryKey[1]) {
  if (filters.status && report.status !== filters.status) return false
  if (filters.severity && report.severity !== filters.severity) return false
  return true
}

export function useReportWebSocket() {
  const queryClient = useQueryClient()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const ws = new WebSocket(`${reportsWebSocketUrl}/ws/${token}`)

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as ReportEvent

      queryClient.invalidateQueries({ queryKey: ['analytics-summary'] })

      queryClient.getQueryCache().findAll({ queryKey: ['reports'] }).forEach((query) => {
        const [, filters] = query.queryKey as ReportsQueryKey
        const matchesFilters = reportMatchesFilters(message.data, filters)

        queryClient.setQueryData<ReportListResponse>(query.queryKey, (current) => {
          if (!current) return current

          if (message.type === 'CREATED') {
            if (!matchesFilters || filters.page !== 1 || current.items.some((report) => report.id === message.data.id)) {
              return current
            }

            return {
              ...current,
              items: [message.data, ...current.items].slice(0, current.page_size),
              total: current.total + 1,
              total_pages: Math.ceil((current.total + 1) / current.page_size),
            }
          }

          if (message.type === 'UPDATED') {
            const existing = current.items.find((report) => report.id === message.data.id)
            if (!existing && matchesFilters && filters.page === 1) {
              return {
                ...current,
                items: [message.data, ...current.items].slice(0, current.page_size),
                total: current.total + 1,
                total_pages: Math.ceil((current.total + 1) / current.page_size),
              }
            }

            if (!existing) return current

            if (!matchesFilters) {
              const nextTotal = Math.max(current.total - 1, 0)
              return {
                ...current,
                items: current.items.filter((report) => report.id !== message.data.id),
                total: nextTotal,
                total_pages: Math.ceil(nextTotal / current.page_size),
              }
            }

            if (!isNewerReport(message.data, existing)) return current
            return {
              ...current,
              items: current.items.map((report) => (report.id === message.data.id ? message.data : report)),
            }
          }

          if (message.type === 'DELETED') {
            if (!current.items.some((report) => report.id === message.data.id)) return current
            const nextTotal = Math.max(current.total - 1, 0)
            return {
              ...current,
              items: current.items.filter((report) => report.id !== message.data.id),
              total: nextTotal,
              total_pages: Math.ceil(nextTotal / current.page_size),
            }
          }

          return current
        })
      })

      queryClient.getQueryCache().findAll({ queryKey: ['map-reports'] }).forEach((query) => {
        const [, filters] = query.queryKey as MapReportsQueryKey
        const matchesStatus = !filters.status || message.data.status === filters.status

        queryClient.setQueryData<Report[]>(query.queryKey, (current) => {
          const currentItems = current ?? []
          const existing = currentItems.find((report) => report.id === message.data.id)

          if (message.type === 'CREATED') {
            if (!matchesStatus || existing) return currentItems
            return [message.data, ...currentItems]
          }

          if (message.type === 'UPDATED') {
            if (existing && !matchesStatus) {
              return currentItems.filter((report) => report.id !== message.data.id)
            }
            if (!existing && !matchesStatus) return currentItems
            if (!existing && matchesStatus) return [message.data, ...currentItems]
            if (!existing) return currentItems
            if (!isNewerReport(message.data, existing)) return currentItems
            return currentItems.map((report) => (report.id === message.data.id ? message.data : report))
          }

          if (message.type === 'DELETED') {
            if (!existing) return currentItems
            return currentItems.filter((report) => report.id !== message.data.id)
          }

          return currentItems
        })
      })
    }

    return () => ws.close()
  }, [queryClient])
}
