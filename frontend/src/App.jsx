import { useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Inventory from './pages/Inventory'
import Sales from './pages/Sales'
import Products from './pages/Products'
import Seasonal from './pages/Seasonal'
import Reports from './pages/Reports'
import Login from './pages/Login'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './components/ToastContext'
import { onUnauthorized } from './api/client'

function GlobalAuthWatcher() {
  const { logout } = useAuth()
  const nav = useNavigate()
  useEffect(() => {
    onUnauthorized(() => { logout(); nav('/login', { replace: true }) })
  }, [logout, nav])
  return null
}

function Shell() {
  const { isAuthenticated } = useAuth()
  const loc = useLocation()
  const isLogin = loc.pathname === '/login'
  if (isLogin || !isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main">
        <Topbar />
        <Routes>
          <Route path="/"          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/forecast"  element={<ProtectedRoute><Forecast /></ProtectedRoute>} />
          <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
          <Route path="/sales"     element={<ProtectedRoute><Sales /></ProtectedRoute>} />
          <Route path="/products"  element={<ProtectedRoute><Products /></ProtectedRoute>} />
          <Route path="/seasonal"  element={<ProtectedRoute><Seasonal /></ProtectedRoute>} />
          <Route path="/reports"   element={<ProtectedRoute roles={['admin', 'analyst']}><Reports /></ProtectedRoute>} />
          <Route path="/login"     element={<Navigate to="/" replace />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <GlobalAuthWatcher />
        <Shell />
      </AuthProvider>
    </ToastProvider>
  )
}
