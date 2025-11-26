import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, LoginRequest } from '../types'
import { authApi } from '../api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (data: LoginRequest) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Check if user is already logged in
    checkAuth()
  }, [])
  
  const checkAuth = async () => {
    try {
      const currentUser = await authApi.getCurrentUser()
      setUser(currentUser)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }
  
  const login = async (data: LoginRequest) => {
    const response = await authApi.login(data)
    setUser(response.user)
  }
  
  const logout = async () => {
    await authApi.logout()
    setUser(null)
  }
  
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
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

