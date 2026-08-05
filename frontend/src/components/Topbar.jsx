import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { LogOut, Sun, Moon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from './ToastContext'

function getInitialTheme() {
  const attr = typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme')
  if (attr) return attr
  try { return localStorage.getItem('theme') || 'light' } catch { return 'light' }
}

const TITLES = {
  '/':          { title: 'Dashboard',          sub: 'Real-time KPIs, sales trends, and inventory health' },
  '/forecast':  { title: 'Demand Forecast',    sub: 'Prophet, XGBoost, and LSTM with confidence intervals' },
  '/inventory': { title: 'Inventory',          sub: 'Stock levels and AI-driven reorder recommendations' },
  '/sales':     { title: 'Sales Records',      sub: 'Daily history used as training input for forecasts' },
  '/products':  { title: 'Products',           sub: 'Manage your SKU catalogue' },
  '/seasonal':  { title: 'Seasonal Analysis',  sub: 'Detect weekly/monthly demand patterns' },
  '/reports':   { title: 'Reports',            sub: 'Generate and download JSON/CSV reports' },
  '/login':     { title: 'Sign in',            sub: 'Access the dashboard' },
}

export default function Topbar() {
  const { user, logout } = useAuth()
  const toast = useToast()
  const loc = useLocation()
  const nav = useNavigate()
  const meta = TITLES[loc.pathname] || { title: 'Page', sub: '' }
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('theme', theme) } catch { /* ignore */ }
  }, [theme])

  const toggleTheme = () => setTheme(t => (t === 'dark' ? 'light' : 'dark'))

  const initials = (user?.username || '?').slice(0, 2).toUpperCase()
  return (
    <div className="topbar">
      <div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Retail Demand Forecasting</div>
        <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text)' }}>{meta.title}</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label="Toggle color theme"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <div className="user">
        <div className="avatar">{initials}</div>
        <div>
          <div style={{ fontWeight: 600, lineHeight: 1.1 }}>{user?.full_name || user?.username}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'capitalize' }}>{user?.role}</div>
        </div>
        <button onClick={() => { logout(); toast.info('Signed out'); nav('/login') }} title="Sign out">
          <LogOut size={14} />
        </button>
        </div>
      </div>
    </div>
  )
}
