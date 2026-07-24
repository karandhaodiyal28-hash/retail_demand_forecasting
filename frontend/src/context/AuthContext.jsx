import { createContext, useContext, useEffect, useState, useCallback } from 'react'

const AuthContext = createContext(null)

const STORAGE_KEY = 'retail_forecast_auth'

const readStored = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.access_token || !parsed?.user) return null
    return parsed
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => readStored())

  useEffect(() => {
    if (auth) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [auth])

  const login = useCallback((payload) => {
    setAuth(payload)
  }, [])

  const logout = useCallback(() => {
    setAuth(null)
  }, [])

  const isAuthenticated = !!auth?.access_token
  const isAdmin = auth?.user?.role === 'admin'
  const isAnalyst = auth?.user?.role === 'analyst' || isAdmin
  const isViewer = auth?.user?.role === 'viewer' || isAnalyst

  return (
    <AuthContext.Provider value={{ auth, user: auth?.user ?? null, isAuthenticated, isAdmin, isAnalyst, isViewer, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
