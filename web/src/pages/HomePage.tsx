import { FormEvent, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { MessageSquare, Shield, Smartphone, Trash2 } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'

export default function HomePage() {
  const { user, loading, requestOtp, loginWithOtp, logout } = useAuth()
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [devOtp, setDevOtp] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [otpRequested, setOtpRequested] = useState(false)
  const [sendingOtp, setSendingOtp] = useState(false)
  const [verifyingOtp, setVerifyingOtp] = useState(false)

  const isAdmin = user?.role === 'admin'

  const helperText = useMemo(() => {
    if (!otpRequested) {
      return 'Enter your phone number to receive a one-time code. If your account does not exist yet, it will be created automatically after verification.'
    }
    return `Enter the 6-digit code sent to ${phone}.`
  }, [otpRequested, phone])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-400" />
      </div>
    )
  }

  if (isAdmin) {
    return <Navigate to="/admin" replace />
  }

  const handleRequestOtp = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSendingOtp(true)

    try {
      const response = await requestOtp(phone)
      setOtpRequested(true)
      setDevOtp(response.otp ?? '')
      setMessage(response.otp ? `OTP sent. Dev OTP: ${response.otp}` : response.message)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setSendingOtp(false)
    }
  }

  const handleVerifyOtp = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setVerifyingOtp(true)

    try {
      const signedInUser = await loginWithOtp(phone, otp)
      if (signedInUser.role === 'admin') {
        logout()
        setError('Administrator accounts must use the admin portal.')
        return
      }
      setMessage(`Signed in successfully as ${signedInUser.full_name || 'user'}.`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setVerifyingOtp(false)
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#dcfce7,transparent_35%),linear-gradient(180deg,#020617_0%,#0f172a_45%,#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col justify-between gap-12 px-4 py-8 sm:px-6 lg:flex-row lg:items-center lg:px-8">
        <section className="max-w-2xl space-y-8">
          <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-emerald-100 backdrop-blur">
            <Trash2 className="h-4 w-4" />
            CleanJO Citizen Access
          </div>

          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
              Report waste faster with a phone number and one-time code.
            </h1>
            <p className="max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              Citizens sign in on this homepage using OTP. New phone numbers are automatically registered after verification.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <FeatureCard icon={Smartphone} title="Phone First" text="No password required for citizen access." />
            <FeatureCard icon={MessageSquare} title="OTP Verify" text="Request a code and verify in the same page." />
            <FeatureCard icon={Shield} title="Admin Separate" text="Administrators sign in from a dedicated route." />
          </div>
        </section>

        <section className="w-full max-w-md rounded-3xl border border-white/10 bg-white/10 p-6 shadow-2xl backdrop-blur-xl sm:p-8">
          <div className="mb-6 space-y-2">
            <h2 className="text-2xl font-semibold text-white">Citizen Login</h2>
            <p className="text-sm leading-6 text-slate-300">{helperText}</p>
          </div>

          {error && (
            <div className="mb-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              {error}
            </div>
          )}

          {message && (
            <div className="mb-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              {message}
            </div>
          )}

          {user ? (
            <div className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
                <p className="text-sm text-slate-300">Signed in as</p>
                <p className="mt-1 text-lg font-medium text-white">{user.full_name || user.phone || user.email}</p>
                <p className="mt-1 text-sm text-slate-400">Role: {user.role}</p>
              </div>
              <button
                type="button"
                onClick={logout}
                className="w-full rounded-2xl border border-white/15 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/10"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <>
              <form onSubmit={handleRequestOtp} className="space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-200">Phone Number</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-primary-400 focus:ring-2 focus:ring-primary-400"
                    placeholder="+9627..."
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={sendingOtp || !phone.trim()}
                  className="w-full rounded-2xl bg-primary-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {sendingOtp ? 'Sending OTP...' : otpRequested ? 'Resend OTP' : 'Send OTP'}
                </button>
              </form>

              {otpRequested && (
                <form onSubmit={handleVerifyOtp} className="mt-4 space-y-4 border-t border-white/10 pt-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-slate-200">One-Time Password</label>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      className="w-full rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-primary-400 focus:ring-2 focus:ring-primary-400"
                      placeholder={devOtp || '6-digit code'}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={verifyingOtp || otp.length !== 6}
                    className="w-full rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {verifyingOtp ? 'Verifying...' : 'Verify and Sign In'}
                  </button>
                </form>
              )}
            </>
          )}

          <div className="mt-6 border-t border-white/10 pt-4 text-sm text-slate-300">
            Admin user?{' '}
            <Link to="/admin/login" className="font-medium text-primary-300 hover:text-primary-200">
              Open the admin portal
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
