import { Link, Navigate } from 'react-router-dom'
import { BarChart3, Shield, Smartphone, Trash2 } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'

export default function HomePage() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-400" />
      </div>
    )
  }

  if (user?.role === 'admin') {
    return <Navigate to="/admin" replace />
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#dcfce7,transparent_35%),linear-gradient(180deg,#020617_0%,#0f172a_45%,#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col justify-between gap-12 px-4 py-8 sm:px-6 lg:flex-row lg:items-center lg:px-8">
        <section className="max-w-2xl space-y-8">
          <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-emerald-100 backdrop-blur">
            <Trash2 className="h-4 w-4" />
            CleanJO Admin Portal
          </div>

          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Monitor reports, activity, and cleanup performance in one place.
            </h1>
            <p className="max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              This web application is reserved for administrators. Citizen access and garbage submission happen in the mobile app using phone number verification with OTP.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <FeatureCard icon={BarChart3} title="Statistics" text="Review dashboards, trends, and operational insights." />
            <FeatureCard icon={Shield} title="Admin Only" text="Password-based access is limited to administrator accounts." />
            <FeatureCard icon={Smartphone} title="Mobile OTP" text="Citizens register and sign in from the mobile app with phone OTP." />
          </div>
        </section>

        <section className="w-full max-w-md rounded-3xl border border-white/10 bg-white/10 p-6 shadow-2xl backdrop-blur-xl sm:p-8">
          <div className="mb-6 space-y-2">
            <h2 className="text-2xl font-semibold text-white">Administrator Access</h2>
            <p className="text-sm leading-6 text-slate-300">
              Use the admin login to open dashboards, reports, maps, and system controls. OTP-based citizen sign-in is intentionally unavailable on the web portal.
            </p>
          </div>

          <div className="space-y-4">
            <Link
              to="/admin/login"
              className="block w-full rounded-2xl bg-primary-500 px-4 py-3 text-center text-sm font-medium text-white transition hover:bg-primary-600"
            >
              Open Admin Login
            </Link>
            <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4 text-sm leading-6 text-slate-300">
              Mobile users should register and sign in from the smartphone app with a phone number and one-time password. The web portal does not provide citizen OTP flows.
            </div>
          </div>

          <div className="mt-6 border-t border-white/10 pt-4 text-sm text-slate-300">
            Already have an administrator account?{' '}
            <Link to="/admin/login" className="font-medium text-primary-300 hover:text-primary-200">
              Sign in here
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}

function FeatureCard({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Smartphone
  title: string
  text: string
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
      <Icon className="h-5 w-5 text-primary-300" />
      <h3 className="mt-3 text-sm font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-300">{text}</p>
    </div>
  )
}
