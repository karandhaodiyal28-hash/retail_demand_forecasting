import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { LogIn, UserPlus, TrendingUp, Eye, EyeOff, BarChart3, ShieldCheck, Zap, Heart, Code2 } from 'lucide-react'
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

  // Set light theme on the login page
  useEffect(() => {
    const prev = document.documentElement.getAttribute('data-theme')
    document.documentElement.setAttribute('data-theme', 'light')
    return () => {
      // Restore previous theme when leaving login
      const saved = localStorage.getItem('theme') || 'light'
      document.documentElement.setAttribute('data-theme', saved)
    }
  }, [])

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

  const features = [
    { icon: BarChart3, title: 'AI-Powered Forecasts', desc: 'Prophet, XGBoost & LSTM models' },
    { icon: Zap, title: 'Real-time Insights', desc: 'Live KPIs and trend analysis' },
    { icon: ShieldCheck, title: 'Smart Inventory', desc: 'Automated reorder recommendations' },
  ]

  return (
    <div className="login-page">
      {/* ── Left hero panel ── */}
      <div className="login-hero">
        <div className="login-hero-content">
          <div className="login-hero-brand">
            <span className="login-hero-logo"><TrendingUp size={22} /></span>
            <span className="login-hero-logo-text">RetailForecast</span>
          </div>

          <h2 className="login-hero-title">
            Predict demand.<br />Optimize inventory.<br />Grow revenue.
          </h2>
          <p className="login-hero-subtitle">
            Enterprise-grade demand forecasting powered by machine learning, delivering actionable insights for smarter retail decisions.
          </p>

          <div className="login-hero-features">
            {features.map(({ icon: Icon, title, desc }) => (
              <div className="login-hero-feature" key={title}>
                <div className="login-hero-feature-icon"><Icon size={18} /></div>
                <div>
                  <div className="login-hero-feature-title">{title}</div>
                  <div className="login-hero-feature-desc">{desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Developer credit on hero */}
          <div className="login-hero-credit">
            <Code2 size={14} />
            <span>Designed & Developed by <strong>Karan Dhaodiyal</strong></span>
          </div>
        </div>

        {/* Decorative floating shapes */}
        <div className="login-hero-orb login-hero-orb-1" />
        <div className="login-hero-orb login-hero-orb-2" />
        <div className="login-hero-orb login-hero-orb-3" />
      </div>

      {/* ── Right form panel ── */}
      <div className="login-form-panel">
        <div className="login-form-wrapper">
          <div className="login-form-header">
            <h1>{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
            <p>
              {mode === 'login'
                ? 'Enter your credentials to access your dashboard'
                : 'Fill in your details to get started'}
            </p>
          </div>

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
                    placeholder="Your full name"
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

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? <span className="spinner" /> : (mode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />)}
              {loading ? (mode === 'login' ? 'Signing in…' : 'Creating…') : (mode === 'login' ? 'Sign in' : 'Create account')}
            </button>
          </form>

          {mode === 'login' && (
            <div className="login-hint">
              <ShieldCheck size={14} />
              <span><strong>Demo:</strong> admin / Admin@123</span>
            </div>
          )}

          <div className="login-switch">
            {mode === 'login' ? (
              <>New here? <a onClick={() => { setError(null); setMode('register') }}>Create an account</a></>
            ) : (
              <>Already have an account? <a onClick={() => { setError(null); setMode('login') }}>Sign in</a></>
            )}
          </div>

          {/* Footer credit */}
          <div className="login-form-footer">
            <span>Made with</span>
            <Heart size={12} className="login-heart" />
            <span>by <strong>Karan Dhaodiyal</strong></span>
            <span className="login-form-footer-dot">•</span>
            <span>Thank you for using RetailForecast</span>
          </div>
        </div>
      </div>
    </div>
  )
}
