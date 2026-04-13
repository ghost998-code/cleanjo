import { FormEvent, useEffect, useState } from 'react'
import { Bell, Shield, SlidersHorizontal, UserCircle2 } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'
import api from '../services/api'
import { AdminPreferences, AdminSettingsResponse } from '../types'

type AdminSettings = {
  fullName: string
  preferences: AdminPreferences
}

const defaultSettings: AdminSettings = {
  fullName: '',
  preferences: {
    notify_on_critical: true,
    compact_report_cards: false,
    auto_refresh_map: true,
  },
}

export default function SettingsPage() {
  const { user, updateUser } = useAuth()
  const [settings, setSettings] = useState<AdminSettings>(defaultSettings)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get<AdminSettingsResponse>('/users/me/settings')
      .then((response) => {
        setSettings({
          fullName: response.data.full_name || '',
          preferences: response.data.preferences,
        })
      })
      .catch((requestError: any) => {
        setError(requestError.response?.data?.detail || 'Failed to load admin settings')
      })
      .finally(() => setLoading(false))
  }, [])

  const updatePreference = <K extends keyof AdminPreferences>(key: K, value: AdminPreferences[K]) => {
    setSettings((current) => ({
      ...current,
      preferences: {
        ...current.preferences,
        [key]: value,
      },
    }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)

    try {
      const response = await api.patch<AdminSettingsResponse>('/users/me/settings', {
        full_name: settings.fullName.trim(),
        preferences: settings.preferences,
      })

      setSettings({
        fullName: response.data.full_name || '',
        preferences: response.data.preferences,
      })
      updateUser({ full_name: response.data.full_name })
      setSavedAt(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Failed to save admin settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[28px] bg-slate-950 text-white shadow-xl shadow-slate-300/40">
        <div className="grid gap-6 px-6 py-8 sm:px-8 lg:grid-cols-[1.4fr_0.9fr] lg:px-10">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.3em] text-primary-300">
              Settings
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Keep the admin panel aligned with your workflow
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Manage the administrator profile name and panel behavior used while
              reviewing submitted reports.
            </p>
            {savedAt && (
              <p className="mt-4 text-sm text-primary-200">Last saved at {savedAt}</p>
            )}
          </div>

          <div className="rounded-[24px] border border-white/10 bg-white/5 p-5 backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-white/10 p-2">
                <UserCircle2 className="h-5 w-5 text-primary-200" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Signed-in admin</p>
                <p className="font-medium text-white">{user?.full_name || 'Administrator'}</p>
              </div>
            </div>
            <dl className="mt-5 space-y-3 text-sm">
              <div className="flex items-center justify-between gap-4 border-t border-white/10 pt-3">
                <dt className="text-slate-400">Role</dt>
                <dd className="font-medium capitalize text-white">{user?.role || 'admin'}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-t border-white/10 pt-3">
                <dt className="text-slate-400">Phone</dt>
                <dd className="font-medium text-white">{user?.phone || '-'}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-t border-white/10 pt-3">
                <dt className="text-slate-400">Email</dt>
                <dd className="truncate font-medium text-white">{user?.email || '-'}</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <form onSubmit={handleSubmit} className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-primary-50 p-3 text-primary-700">
              <SlidersHorizontal className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                Workspace preferences
              </h2>
              <p className="text-sm text-slate-500">
                Persisted controls for the admin panel experience.
              </p>
            </div>
          </div>

          {error && (
            <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-8 rounded-3xl border border-slate-200 p-5">
            <label className="block text-sm font-medium text-slate-700">Admin display name</label>
            <input
              type="text"
              value={settings.fullName}
              onChange={(event) => setSettings((current) => ({ ...current, fullName: event.target.value }))}
              placeholder="Administrator name"
              disabled={loading || saving}
              className="mt-3 w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-primary-500 focus:ring-2 focus:ring-primary-200 disabled:cursor-not-allowed disabled:bg-slate-50"
            />
          </div>

          <div className="mt-8 space-y-4">
            <PreferenceRow
              title="Critical report alerts"
              description="Highlight urgent incoming reports for rapid triage."
              checked={settings.preferences.notify_on_critical}
              onChange={(checked) => updatePreference('notify_on_critical', checked)}
              icon={<Bell className="h-5 w-5" />}
              disabled={loading || saving}
            />
            <PreferenceRow
              title="Compact report layout"
              description="Prefer denser report views when reviewing large daily volumes."
              checked={settings.preferences.compact_report_cards}
              onChange={(checked) => updatePreference('compact_report_cards', checked)}
              icon={<SlidersHorizontal className="h-5 w-5" />}
              disabled={loading || saving}
            />
            <PreferenceRow
              title="Map auto refresh"
              description="Prepare the map workspace for live activity refresh behavior."
              checked={settings.preferences.auto_refresh_map}
              onChange={(checked) => updatePreference('auto_refresh_map', checked)}
              icon={<Shield className="h-5 w-5" />}
              disabled={loading || saving}
            />
          </div>

          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              disabled={loading || saving}
              className="rounded-2xl bg-primary-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? 'Saving...' : 'Save settings'}
            </button>
          </div>
        </form>

        <div className="space-y-6">
          <div className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                  Security status
                </h2>
                <p className="text-sm text-slate-500">Current access assumptions for this panel.</p>
              </div>
            </div>

            <div className="mt-6 space-y-4 text-sm text-slate-600">
              <div className="rounded-2xl bg-slate-50 p-4">
                Admin access is enforced in the frontend route layer and by backend admin-only endpoints.
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                Preferences on this page are now persisted on the signed-in admin user record.
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                Email and phone remain read-only until verified update flows are added.
              </div>
            </div>
          </div>

          <div className="rounded-[28px] border border-primary-200 bg-primary-50 p-6 sm:p-8">
            <h2 className="text-lg font-semibold tracking-tight text-primary-900">
              Next backend hookup
            </h2>
            <p className="mt-3 text-sm leading-6 text-primary-800">
              This screen is now backed by the API and can be extended with richer
              organization-level controls when those contracts are defined.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

function PreferenceRow({
  title,
  description,
  checked,
  onChange,
  icon,
  disabled,
}: {
  title: string
  description: string
  checked: boolean
  onChange: (checked: boolean) => void
  icon: React.ReactNode
  disabled?: boolean
}) {
  return (
    <label className={`flex items-start justify-between gap-4 rounded-3xl border border-slate-200 p-5 transition ${disabled ? 'cursor-not-allowed opacity-70' : 'cursor-pointer hover:border-primary-300 hover:bg-primary-50/40'}`}>
      <div className="flex gap-4">
        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">{icon}</div>
        <div>
          <p className="font-medium text-slate-900">{title}</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
        </div>
      </div>
      <div className="pt-1">
        <span
          className={`flex h-7 w-12 items-center rounded-full p-1 transition ${
            checked ? 'bg-primary-500' : 'bg-slate-300'
          }`}
        >
          <input
            type="checkbox"
            checked={checked}
            onChange={(event) => onChange(event.target.checked)}
            disabled={disabled}
            className="sr-only"
          />
          <span
            className={`h-5 w-5 rounded-full bg-white transition ${
              checked ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </span>
      </div>
    </label>
  )
}
