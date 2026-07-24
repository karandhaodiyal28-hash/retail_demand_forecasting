import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Package, BarChart3,
  ShoppingCart, FileText, Boxes, LogOut,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from './ToastContext'

const navItems = [
  { to: '/',          label: 'Dashboard',         icon: LayoutDashboard, roles: ['admin', 'analyst', 'viewer'] },
  { to: '/forecast',  label: 'Demand Forecast',   icon: TrendingUp,      roles: ['admin', 'analyst', 'viewer'] },
  { to: '/inventory', label: 'Inventory',         icon: Boxes,           roles: ['admin', 'analyst', 'viewer'] },
  { to: '/sales',     label: 'Sales',             icon: ShoppingCart,    roles: ['admin', 'analyst', 'viewer'] },
  { to: '/products',  label: 'Products',          icon: Package,         roles: ['admin', 'analyst', 'viewer'] },
  { to: '/seasonal',  label: 'Seasonal Analysis', icon: BarChart3,       roles: ['admin', 'analyst', 'viewer'] },
  { to: '/reports',   label: 'Reports',           icon: FileText,        roles: ['admin', 'analyst'] },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const toast = useToast()
  const role = user?.role

  const visible = navItems.filter((n) => !role || n.roles.includes(role))

  return (
    <aside className="sidebar">
      <div className="brand">
        <h1>Retail Demand</h1>
        <p className="subtitle">Forecasting System</p>
      </div>

      <nav style={{ flex: 1 }}>
        {visible.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="icon"><Icon size={18} /></span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <div style={{ color: 'var(--text)', fontWeight: 600 }}>{user?.username}</div>
            <div style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>{user?.role}</div>
          </div>
          <button
            className="secondary"
            style={{ padding: '0.4rem 0.6rem' }}
            onClick={() => { logout(); toast.info('Signed out') }}
            title="Sign out"
          >
            <LogOut size={14} />
          </button>
        </div>
        <div>v{import.meta.env.VITE_APP_VERSION || '1.1.0'}</div>
      </div>
    </aside>
  )
}
