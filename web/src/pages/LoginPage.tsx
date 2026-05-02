import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Lock, ShieldCheck, Trash2, User } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { loginWithPassword } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await loginWithPassword(identifier, password)
      navigate('/admin')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#14532d,transparent_35%),linear-gradient(180deg,#020617_0%,#03120a_48%,#0b1f16_100%)] px-4 py-10 text-white">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="space-y-8">
          <div className="inline-flex items-center gap-3 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-100 backdrop-blur">
            <Trash2 className="h-4 w-4" />
            CleanJO Command Center
          </div>

          <div className="space-y-4">
            <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Uber-style ops visibility for every cleanup report across Jordan.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-emerald-50/78 sm:text-lg">
              Sign in with an administrator account to review incoming reports, inspect live map activity, and coordinate response from one green operations dashboard.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <PortalFeature title="Live map" text="Pinned reports update inside a city-scale dark map." />
            <PortalFeature title="Admin only" text="Citizen OTP flows remain in the mobile app." />
            <PortalFeature title="Fast triage" text="Severity, status, and trends surface immediately." />
          </div>
        </section>

        <div className="rounded-[2rem] border border-white/10 bg-white/8 p-6 shadow-[0_30px_120px_rgba(3,7,18,0.55)] backdrop-blur-2xl sm:p-8">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.28em] text-emerald-200/80">
                Admin Login
              </p>
              <h2 className="mt-3 text-3xl font-semibold text-white">Welcome back</h2>
              <p className="mt-3 text-sm leading-6 text-emerald-50/70">
                Use your administrator email or phone number and password to continue.
              </p>
            </div>
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-emerald-100">
              <ShieldCheck className="h-6 w-6" />
            </div>
          </div>

          {error && (
            <div className="mb-6 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-emerald-50/90">
                Email or Phone Number
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-100/40" />
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/35 py-3 pl-10 pr-4 text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
                  placeholder="admin@example.com or +9627..."
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-emerald-50/90">
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-100/40" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-slate-950/35 py-3 pl-10 pr-4 text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/30"
                  placeholder="Your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !identifier.trim() || !password}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-4 py-3 font-medium text-slate-950 transition hover:bg-emerald-400 focus:ring-4 focus:ring-emerald-200/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent"></div>
                  Signing in...
                </span>
              ) : (
                <>
                  Continue to dashboard
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/30 p-4 text-sm leading-6 text-emerald-50/70">
            The web portal is restricted to administrators. Citizens should continue using the mobile app for OTP-based registration and reporting.
          </div>

          <p className="mt-6 text-center text-sm text-emerald-50/65">
            <Link to="/" className="font-medium text-emerald-300 hover:text-emerald-200">
              Back to portal overview
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

function PortalFeature({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-[1.75rem] border border-white/10 bg-white/6 p-5 backdrop-blur">
      <p className="text-sm font-semibold uppercase tracking-[0.22em] text-emerald-200/70">{title}</p>
      <p className="mt-3 text-sm leading-6 text-emerald-50/70">{text}</p>
    </div>
  )
}
