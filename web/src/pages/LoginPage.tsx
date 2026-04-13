import { FormEvent, useState } from 'react'
import { Trash2, X } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'
import api from '../services/api'

export default function LoginPage() {
  const { login } = useAuth()
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [devOtp, setDevOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)
  const [otpModalOpen, setOtpModalOpen] = useState(false)

  const requestOtp = async () => {
    setError('')
    setMessage('')
    setDevOtp('')
    setOtpLoading(true)

    try {
      const response = await api.post('/auth/request-phone-otp', { phone })
      setMessage(response.data.otp ? `OTP sent. Dev OTP: ${response.data.otp}` : 'OTP sent to your phone number.')
      setDevOtp(response.data.otp ?? '')
      setOtp('')
      setOtpModalOpen(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setOtpLoading(false)
    }
  }

  const handleRequestOtp = async (e: FormEvent) => {
    e.preventDefault()
    await requestOtp()
  }

  const handleVerifyOtp = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      await login(phone, otp)
      window.location.href = '/'
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  const closeOtpModal = () => {
    setError('')
    setOtp('')
    setOtpModalOpen(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="flex items-center justify-center mb-6">
          <div className="bg-primary-100 p-3 rounded-full">
            <Trash2 className="w-8 h-8 text-primary-600" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">
          Garbage Detection
        </h1>
        <p className="text-center text-gray-500 mb-8">
          Enter your phone number to continue. New users get an automatic name and can update it later.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {message && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
            {message}
          </div>
        )}

        <form onSubmit={handleRequestOtp} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
              placeholder="+12345678901"
              required
            />
          </div>

          <button
            type="submit"
            disabled={otpLoading || !phone.trim()}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-primary-700 focus:ring-4 focus:ring-primary-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {otpLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Sending OTP...
              </span>
            ) : (
              'Continue'
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          We will verify your phone number with a one-time code.
        </p>
      </div>

      {otpModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Enter OTP</h2>
                <p className="mt-1 text-sm text-gray-500">
                  Enter the 6-digit code sent to {phone}.
                </p>
              </div>
              <button
                type="button"
                onClick={closeOtpModal}
                className="rounded-lg p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
                aria-label="Close OTP dialog"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OTP
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  autoFocus
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                  placeholder={devOtp || '6-digit code'}
                  required
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={requestOtp}
                  disabled={otpLoading || !phone.trim()}
                  className="flex-1 rounded-lg border border-primary-200 px-4 py-3 text-sm font-medium text-primary-700 transition hover:bg-primary-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {otpLoading ? 'Sending...' : 'Resend OTP'}
                </button>
                <button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="flex-1 rounded-lg bg-primary-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? 'Verifying...' : 'Verify'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
