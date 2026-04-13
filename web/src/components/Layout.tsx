import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard,
  FileText,
  Map,
  Settings,
  LogOut,
  Trash2,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/reports', icon: FileText, label: 'Reports' },
  { path: '/map', icon: Map, label: 'Map' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const displayName = user?.full_name || 'Citizen'
  const subtitle = user?.phone || user?.email || ''
  const avatarLabel = displayName[0]?.toUpperCase() || user?.phone?.[0] || 'C'
  const currentPage = navItems.find((item) => item.path === location.pathname)?.label || 'Admin Panel'

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 lg:flex">
      <div
        className={clsx(
          'fixed inset-0 z-40 bg-slate-950/50 transition lg:hidden',
          mobileMenuOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'
        )}
        onClick={() => setMobileMenuOpen(false)}
      />

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex w-80 max-w-[85vw] flex-col border-r border-white/10 bg-slate-950 text-white transition-transform lg:static lg:z-auto lg:w-72 lg:max-w-none lg:translate-x-0',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="border-b border-white/10 p-6">
          <div className="flex items-center justify-between gap-3 lg:block">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-primary-500/15 p-3 ring-1 ring-primary-400/20">
                <Trash2 className="h-6 w-6 text-primary-300" />
              </div>
              <div>
                <h1 className="font-semibold tracking-tight text-white">CleanJO Admin</h1>
                <p className="text-xs text-slate-400">Field report command center</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-xl p-2 text-slate-400 transition hover:bg-white/10 hover:text-white lg:hidden"
              aria-label="Close navigation"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="border-b border-white/10 px-4 py-4">
          <div className="rounded-2xl bg-white/5 p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-primary-500/15 p-2 text-primary-300">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Administrator workspace</p>
                <p className="text-xs text-slate-400">Monitor incoming reports and response flow</p>
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = item.path === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.path)
            
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={clsx(
                  'flex items-center gap-3 rounded-2xl px-4 py-3 font-medium transition',
                  isActive
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-900/20'
                    : 'text-slate-300 hover:bg-white/8 hover:text-white'
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
              <span className="font-bold text-white">
                {avatarLabel}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate font-medium text-white">
                {displayName}
              </p>
              <p className="truncate text-xs text-slate-400">{subtitle}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium text-rose-300 transition hover:bg-rose-500/10 hover:text-rose-200"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-slate-100/90 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(true)}
                className="rounded-xl border border-slate-200 bg-white p-2 text-slate-700 shadow-sm transition hover:bg-slate-50 lg:hidden"
                aria-label="Open navigation"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-500">
                  Admin Panel
                </p>
                <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                  {currentPage}
                </h2>
              </div>
            </div>
            <div className="hidden rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm sm:block">
              Signed in as <span className="font-medium text-slate-900">{user?.role}</span>
            </div>
          </div>
        </header>

        <div className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
