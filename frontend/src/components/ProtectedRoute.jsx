import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Wraps a protected route.  Redirects to /login if not authenticated.
 * Pass `roles={['admin', 'analyst']}` to also enforce role-based access.
 */
export default function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, user } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (roles && roles.length > 0 && !roles.includes(user?.role)) {
    return (
      <div className="empty-state">
        <div className="icon" style={{ margin: '0 auto 1rem' }}>🚫</div>
        <h3>Access denied</h3>
        <p className="muted">Your role ({user?.role}) doesn't have permission to view this page.</p>
      </div>
    )
  }
  return children
}
