import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  loading: boolean
  loginWithPassword: (identifier: string, password: string) => Promise<User>
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      api.get('/auth/me')
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const loginWithPassword = async (identifier: string, password: string) => {
    const response = await api.post('/auth/login', { identifier, password })
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
    
    const userResponse = await api.get('/auth/me')
    if (userResponse.data.role !== 'admin') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      throw new Error('Only administrator accounts can access the web portal.')
    }

    setUser(userResponse.data)
    return userResponse.data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  const updateUser = (updates: Partial<User>) => {
    setUser((currentUser) => {
      if (!currentUser) return currentUser
      return { ...currentUser, ...updates }
    })
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithPassword, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
