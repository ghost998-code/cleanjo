import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ReportsPage from './pages/ReportsPage'
import MapPage from './pages/MapPage'
import SettingsPage from './pages/SettingsPage'
import Layout from './components/Layout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()

  if (user?.role !== 'admin') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
        <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-primary-300">
            Admin Panel
          </p>
          <h1 className="mt-4 text-3xl font-semibold">Access restricted</h1>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            This area is only available to administrator accounts. Sign in with an
            admin profile to manage reports, map activity, and panel settings.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              onClick={logout}
              className="rounded-xl bg-primary-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-primary-600"
            >
              Sign out
            </button>
            <a
              href="/login"
              className="rounded-xl border border-white/15 px-4 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/10"
            >
              Back to login
            </a>
          </div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AdminRoute>
                  <Layout />
                </AdminRoute>
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="map" element={<MapPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
