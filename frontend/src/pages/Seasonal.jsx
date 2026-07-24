import { useState, useEffect } from 'react'
import { endpoints } from '../components/useApi'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, Cell } from 'recharts'
import { BarChart3, TrendingUp, TrendingDown, Minus, Calendar, Activity } from 'lucide-react'
import { formatNumber } from '../utils/format'
import { useToast } from '../components/ToastContext'

export default function Seasonal() {
  const [products, setProducts] = useState([])
  const [productId, setProductId] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  useEffect(() => {
    endpoints.listProducts()
      .then((p) => { setProducts(p); if (p.length && !productId) setProductId(p[0].id) })
      .catch((e) => toast.error(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const analyze = async (pid) => {
    setProductId(pid); setError(null); setData(null)
    if (!pid) return
    setLoading(true)
    try { setData(await endpoints.getSeasonal(Number(pid))) }
    catch (e) { setError(e.message); toast.error(e.message) }
    finally { setLoading(false) }
  }

  const weeklyData = data ? Object.entries(data.weekly_pattern || {}).map(([day, v]) => ({ day, value: v })) : []
  const monthlyData = data ? Object.entries(data.monthly_pattern || {}).map(([month, v]) => ({ month: month.slice(0, 3), value: v })) : []
  const trendColor = data?.trend_direction === 'up' ? '#2ecc71' : data?.trend_direction === 'down' ? '#ff5c7a' : '#94a3b8'
  const TrendIcon = data?.trend_direction === 'up' ? TrendingUp : data?.trend_direction === 'down' ? TrendingDown : Minus

  return (
    <div>
      <div className="card">
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: 420 }}>
            <label>Product</label>
            <select value={productId} onChange={(e) => analyze(e.target.value)}>
              <option value="">Select product…</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
            </select>
          </div>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {loading && <div className="loading-overlay"><span className="spinner" /> Analyzing…</div>}
      </div>

      {data && (
        <>
          <div className="grid grid-4">
            <div className="stat-card">
              <div className="icon-pill" style={{ color: trendColor, background: `${trendColor}22` }}>
                <TrendIcon size={20} />
              </div>
              <div className="label">Trend Direction</div>
              <div className="value" style={{ color: trendColor, textTransform: 'uppercase' }}>{data.trend_direction}</div>
              <div className="delta muted">{data.trend_slope_per_day} units/day</div>
            </div>
            <div className="stat-card">
              <div className="icon-pill" style={{ color: '#7f5af0', background: 'rgba(127, 90, 240, 0.15)' }}>
                <Calendar size={20} />
              </div>
              <div className="label">Peak Weekday</div>
              <div className="value" style={{ fontSize: '1.4rem' }}>{data.peak_weekday}</div>
              <div className="delta muted">highest avg demand</div>
            </div>
            <div className="stat-card">
              <div className="icon-pill" style={{ color: '#2cb1bc', background: 'rgba(44, 177, 188, 0.15)' }}>
                <BarChart3 size={20} />
              </div>
              <div className="label">Peak Month</div>
              <div className="value" style={{ fontSize: '1.4rem' }}>{data.peak_month}</div>
              <div className="delta muted">highest avg demand</div>
            </div>
            <div className="stat-card">
              <div className="icon-pill" style={{ color: '#ffb86b', background: 'rgba(255, 184, 107, 0.18)' }}>
                <Activity size={20} />
              </div>
              <div className="label">Avg Daily Demand</div>
              <div className="value">{formatNumber(data.avg_daily)}</div>
              <div className="delta muted">across full history</div>
            </div>
          </div>

          <div className="grid grid-2">
            <div className="card">
              <h3>Weekly Pattern (avg by day of week)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="day" stroke="rgba(244,244,247,0.55)" fontSize={10} />
                  <YAxis stroke="rgba(244,244,247,0.55)" fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} name="Avg quantity">
                    {weeklyData.map((d, i) => (
                      <Cell key={i} fill={d.day === data.peak_weekday ? '#ff6ec7' : '#7f5af0'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3>Monthly Pattern (avg by month)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={monthlyData}>
                  <defs>
                    <linearGradient id="g-monthly" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#2cb1bc" />
                      <stop offset="100%" stopColor="#7f5af0" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="month" stroke="rgba(244,244,247,0.55)" fontSize={10} />
                  <YAxis stroke="rgba(244,244,247,0.55)" fontSize={11} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="url(#g-monthly)" strokeWidth={2.5} dot={{ r: 3, fill: '#7f5af0' }} name="Avg quantity" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <h3>Statistical Summary</h3>
            <div className="grid grid-4">
              <div><div className="muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Max daily</div><div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: 6 }}>{formatNumber(data.max_daily)}</div></div>
              <div><div className="muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Min daily</div><div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: 6 }}>{formatNumber(data.min_daily)}</div></div>
              <div><div className="muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Std deviation</div><div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: 6 }}>{formatNumber(data.std_daily)}</div></div>
              <div><div className="muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Trend slope/day</div><div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: 6 }}>{data.trend_slope_per_day}</div></div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
