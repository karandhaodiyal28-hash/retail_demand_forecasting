import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { LogIn, UserPlus, TrendingUp, Eye, EyeOff } from 'lucide-react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastContext'

export default function Login() {
  const [mode, setMode] = useState('login')                  // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { login, isAuthenticated } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/'

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true })
  }, [isAuthenticated, navigate, from])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(null); setLoading(true)
    try {
      // OAuth2PasswordRequestForm expects form-encoded data
      const body = new URLSearchParams()
      body.append('username', username)
      body.append('password', password)
      const r = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      login(r.data)
      toast.success(`Welcome back, ${r.data.user.full_name || r.data.user.username}!`)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError(null); setLoading(true)
    try {
      await api.post('/auth/register', {
        username,
        password,
        email: email || null,
        full_name: fullName || null,
        role: 'analyst',
      })
      // auto-login after register
      const body = new URLSearchParams()
      body.append('username', username)
      body.append('password', password)
      const r = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      login(r.data)
      toast.success('Account created — welcome aboard!')
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="auth-brand-mark"><TrendingUp size={18} /></span>
          <span className="auth-brand-name">RetailForecast</span>
        </div>
        <h1>{mode === 'login' ? 'Sign in' : 'Create account'}</h1>
        <p className="auth-sub">
          {mode === 'login'
            ? 'Enter your credentials to continue'
            : 'Fill in your details to get started'}
        </p>

        <form onSubmit={mode === 'login' ? handleLogin : handleRegister}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoComplete="username"
            />
          </div>

          {mode === 'register' && (
            <>
              <div className="form-group">
                <label htmlFor="fullName">Full name <span className="muted">(optional)</span></label>
                <input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Karan Dhaodiyal"
                  autoComplete="name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email <span className="muted">(optional)</span></label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="[email protected]"
                  autoComplete="email"
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-affix">
              <input
                id="password"
                type={showPwd ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Min 8 chars, letters + digits' : 'Enter your password'}
                required
                minLength={mode === 'register' ? 8 : 1}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              />
              <button
                type="button"
                className="affix-btn"
                onClick={() => setShowPwd((s) => !s)}
                aria-label={showPwd ? 'Hide password' : 'Show password'}
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && <div className="alert alert-error" role="alert">{error}</div>}

          <button type="submit" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : (mode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />)}
            {loading ? (mode === 'login' ? 'Signing in…' : 'Creating…') : (mode === 'login' ? 'Sign in' : 'Create account')}
          </button>
        </form>

        {mode === 'login' && (
          <div className="hint">
            <strong>Default login:</strong> admin / Admin@123 — please change it after your first sign in.
          </div>
        )}

        <div className="switch-link">
          {mode === 'login' ? (
            <>New here? <a onClick={() => { setError(null); setMode('register') }} style={{ cursor: 'pointer' }}>Create an account</a></>
          ) : (
            <>Already have an account? <a onClick={() => { setError(null); setMode('login') }} style={{ cursor: 'pointer' }}>Sign in</a></>
          )}
        </div>
      </div>
    </div>
  )
}
