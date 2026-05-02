import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { User } from '../types'
import { format } from 'date-fns'
import clsx from 'clsx'
import { useState } from 'react'

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  inspector: 'bg-blue-100 text-blue-700',
  citizen: 'bg-green-100 text-green-700',
}

export default function UsersPage() {
  const [roleFilter, setRoleFilter] = useState('')
  const queryClient = useQueryClient()

  const {
    data: users = [],
    isFetching,
    isError,
  } = useQuery({
    queryKey: ['users', { role: roleFilter }],
    queryFn: async () => {
      const params = roleFilter ? { role: roleFilter } : {}
      const response = await api.get<User[] | { items: User[] }>('/users', { params })
      if (Array.isArray(response.data)) {
        return response.data
      }
      return response.data.items || []
    },
    placeholderData: [],
    retry: 1,
  })

  const { mutate: mutateRole, isPending: isUpdatingRole } = useMutation({
    mutationFn: async ({ userId, newRole }: { userId: string; newRole: string }) => {
      await api.patch(`/users/${userId}/role`, { role: newRole })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const updateRole = (userId: string, newRole: string) => {
    mutateRole({ userId, newRole })
  }

  return (
    <div className="space-y-6">
      {isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load users. Showing available data.
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Users</h1>
          <p className="text-gray-500">{users.length} users</p>
        </div>
      </div>

      <div className="rounded-xl bg-white p-4 shadow-sm">
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="inspector">Inspector</option>
          <option value="citizen">Citizen</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-xl bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Phone
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Joined
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isFetching ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary-600"></div>
                    </div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const name = user.full_name || user.email || user.phone || 'Unknown User'
                  const avatarSeed = (user.email || user.phone || user.full_name || 'u')[0]?.toUpperCase() || 'U'

                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100">
                            <span className="font-bold text-primary-700">{avatarSeed}</span>
                          </div>
                          <span className="font-medium text-gray-800">{name}</span>
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                        {user.email || '-'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span
                          className={clsx(
                            'rounded-full px-2 py-1 text-xs font-medium',
                            ROLE_COLORS[user.role]
                          )}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                        {user.phone || '-'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                        {format(new Date(user.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <select
                          value={user.role}
                          disabled={isUpdatingRole}
                          onChange={(e) => updateRole(user.id, e.target.value)}
                          className="rounded border border-gray-300 px-2 py-1 text-sm focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <option value="citizen">Citizen</option>
                          <option value="inspector">Inspector</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
