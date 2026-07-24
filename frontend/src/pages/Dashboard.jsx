import { useMemo, useState } from 'react'
import { useApi, endpoints } from '../components/useApi'
import {
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts'
import {
  TrendingUp, AlertTriangle, Activity, IndianRupee,
  Download, FileText, ArrowUpRight, ArrowDownRight,
} from 'lucide-react'
import { formatCurrency, formatNumber } from '../utils/format'

const PIE_COLORS = ['#7f5af0', '#2cb1bc', '#ff6ec7', '#ffb86b', '#2ecc71', '#4dabf7', '#ff5c7a']
const DATE_RANGES = [
  { value: 7, label: 'Last 7 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
  { value: 180, label: 'Last 180 days' },
]

const sum = (arr, key) => arr.reduce((s, x) => s + (Number(x[key]) || 0), 0)

function riskFromStatus(status) {
  switch (status) {
    case 'REORDER':   return { level: 'High',   cls: 'badge-high',  action: 'Reorder now' }
    case 'LOW':       return { level: 'Medium', cls: 'badge-med',   action: 'Reorder soon' }
    case 'OVERSTOCK': return { level: 'Low',    cls: 'badge-low',   action: 'Reduce stock' }
    case 'ERROR':     return { level: '—',      cls: 'badge-error', action: 'Needs data' }
    default:          return { level: 'Low',    cls: 'badge-low',   action: 'Healthy' }
  }
}

const csvCell = (v) => {
  const s = String(v ?? '')
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

function exportCSV(rows) {
  const header = ['Product', 'Category', 'Predicted Demand (30d)', 'Recommended Order Qty', 'Risk Level', 'Action Status']
  const lines = [header.join(',')]
  rows.forEach((r) => lines.push([r.name, r.category, r.predicted, r.recommended, r.risk, r.action].map(csvCell).join(',')))
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `demand-forecast-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function Dashboard() {
  const [days, setDays] = useState(30)
  const [cat, setCat] = useState('All')

  const { data: summary, loading, error } = useApi(endpoints.dashboardSummary, [])
  const { data: demand }    = useApi(() => endpoints.demandTrend(days), [days])
  const { data: rev }       = useApi(() => endpoints.revenueTrend(days), [days])
  const { data: cats }      = useApi(endpoints.categoryBreakdown, [])
  const { data: inventory } = useApi(endpoints.listInventory, [])
  const { data: products }  = useApi(endpoints.listProducts, [])

  const productById = useMemo(() => {
    const m = {}
    ;(products || []).forEach((p) => { m[p.id] = p })
    return m
  }, [products])

  const categories = useMemo(() => {
    const set = new Set((products || []).map((p) => p.category).filter(Boolean))
    return ['All', ...Array.from(set).sort()]
  }, [products])

  // ---- KPI derivations -------------------------------------------------
  const hist = demand?.historical || []
  const pred = demand?.predicted || []
  const totalForecast = sum(pred, 'units')
  const histAvg = hist.length ? sum(hist, 'units') / hist.length : 0
  const predAvg = pred.length ? totalForecast / pred.length : 0
  const growth = histAvg > 0 ? ((predAvg - histAvg) / histAvg) * 100 : 0

  const alertCount = (inventory || []).filter((i) => i.status === 'REORDER' || i.status === 'LOW').length

  const volatility = useMemo(() => {
    if (hist.length < 2) return 0
    const mean = histAvg || 1
    const variance = hist.reduce((s, d) => s + Math.pow((d.units || 0) - mean, 2), 0) / hist.length
    return (Math.sqrt(variance) / mean) * 100
  }, [hist, histAvg])

  const revWindow = sum(rev || [], 'revenue')
  const histUnits = sum(hist, 'units')
  const revPerUnit = histUnits > 0 ? revWindow / histUnits : 0
  const projectedRevenue = revPerUnit * totalForecast

  // ---- Data grid rows (join inventory + product) -----------------------
  const gridRows = useMemo(() => {
    return (inventory || [])
      .map((inv) => {
        const p = productById[inv.product_id]
        const category = p?.category || 'Uncategorized'
        const r = riskFromStatus(inv.status)
        return {
          id: inv.product_id,
          name: inv.name,
          category,
          predicted: Math.round((inv.avg_daily_demand || 0) * 30),
          recommended: Math.round(inv.recommended_order_qty || 0),
          risk: r.level,
          riskCls: r.cls,
          action: r.action,
          status: inv.status,
        }
      })
      .filter((r) => cat === 'All' || r.category === cat)
  }, [inventory, productById, cat])

  // ---- Chart datasets --------------------------------------------------
  const demandChart = [
    ...hist.map((d) => ({ date: d.date, historical: d.units })),
    ...pred.map((d) => ({ date: d.date, predicted: d.units })),
  ]

  const invBars = useMemo(() => {
    return (inventory || [])
      .map((inv) => ({ ...inv, category: productById[inv.product_id]?.category || 'Uncategorized' }))
      .filter((inv) => cat === 'All' || inv.category === cat)
      .sort((a, b) => (b.reorder_point || 0) - (a.reorder_point || 0))
      .slice(0, 8)
      .map((inv) => ({
        name: inv.name.length > 14 ? inv.name.slice(0, 13) + '…' : inv.name,
        current: Math.round(inv.current_stock || 0),
        reorder: Math.round(inv.reorder_point || 0),
      }))
  }, [inventory, productById, cat])

  const donutData = cats || []
  const donutTotal = sum(donutData, 'revenue')

  if (loading) return <div className="loading-overlay"><span className="spinner" /> Loading dashboard…</div>
  if (error)   return <div className="alert alert-error">{error}</div>

  const kpis = [
    {
      label: 'Total Forecasted Demand',
      value: formatNumber(Math.round(totalForecast)),
      icon: TrendingUp, color: '#7f5af0', bg: 'rgba(127, 90, 240, 0.15)',
      delta: pred.length ? `${growth >= 0 ? '+' : ''}${growth.toFixed(1)}% vs recent avg` : 'Run forecasts to populate',
      dir: growth > 0.5 ? 'up' : growth < -0.5 ? 'down' : 'flat',
    },
    {
      label: 'Safety Stock Alerts',
      value: formatNumber(alertCount),
      icon: AlertTriangle, color: '#ff5c7a', bg: 'rgba(255, 92, 122, 0.15)',
      delta: alertCount ? 'products need reordering' : 'all products healthy',
      dir: alertCount ? 'down' : 'up',
      badge: alertCount,
    },
    {
      label: 'Demand Volatility Index',
      value: volatility.toFixed(1),
      icon: Activity, color: '#ffb86b', bg: 'rgba(255, 184, 107, 0.18)',
      delta: 'coefficient of variation (%)',
      dir: 'flat',
    },
    {
      label: 'Projected Sales Revenue',
      value: formatCurrency(projectedRevenue),
      icon: IndianRupee, color: '#2ecc71', bg: 'rgba(46, 204, 113, 0.15)',
      delta: `over next ${pred.length || 0} days`,
      dir: 'up',
    },
  ]

  return (
    <div>
      {/* ---- Header + filter bar ---- */}
      <div className="page-header" style={{ marginBottom: '1rem' }}>
        <h2>Executive Analytics</h2>
        <p>Retail Demand &amp; Inventory Analytics</p>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <label>Date Range</label>
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            {DATE_RANGES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label>Product Category</label>
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            {categories.map((c) => <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>)}
          </select>
        </div>
        <div className="spacer" />
        <div className="actions">
          <button className="secondary" onClick={() => exportCSV(gridRows)}>
            <Download size={14} /> Export CSV
          </button>
          <button className="secondary" onClick={() => window.print()}>
            <FileText size={14} /> Export PDF
          </button>
        </div>
      </div>

      {summary?.low_stock_count > 0 && (
        <div className="alert alert-error">
          <AlertTriangle size={16} />
          <span><strong>{summary.low_stock_count}</strong> product(s) below reorder point — review the Inventory page.</span>
        </div>
      )}

      {/* ---- KPI cards ---- */}
      <div className="grid grid-4" style={{ marginBottom: '1.25rem' }}>
        {kpis.map((k, i) => (
          <div className="stat-card" key={i}>
            {k.badge != null
              ? <div className="kpi-badge" style={{ color: k.color, background: k.bg }}>{k.badge}</div>
              : <div className="icon-pill" style={{ color: k.color, background: k.bg }}><k.icon size={20} /></div>}
            <div className="label">{k.label}</div>
            <div className="value">{k.value}</div>
            <div className={`delta ${k.dir}`}>
              {k.dir === 'up' ? <ArrowUpRight size={12} /> : k.dir === 'down' ? <ArrowDownRight size={12} /> : null}
              {k.delta}
            </div>
          </div>
        ))}
      </div>

      {/* ---- Main wide demand chart ---- */}
      <div className="card">
        <h3>Historical Sales vs Predicted Demand</h3>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={demandChart}>
            <defs>
              <linearGradient id="g-hist" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2cb1bc" stopOpacity={0.55} />
                <stop offset="100%" stopColor="#2cb1bc" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="g-pred2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ff6ec7" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#ff6ec7" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" stroke="rgba(244,244,247,0.55)" fontSize={11} minTickGap={28} />
            <YAxis stroke="rgba(244,244,247,0.55)" fontSize={11} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="historical" name="Historical Units" stroke="#2cb1bc" strokeWidth={2} fill="url(#g-hist)" connectNulls={false} />
            <Area type="monotone" dataKey="predicted" name="Predicted Demand" stroke="#ff6ec7" strokeWidth={2.5} strokeDasharray="5 3" fill="url(#g-pred2)" connectNulls={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ---- Two side charts ---- */}
      <div className="grid grid-2">
        <div className="card">
          <h3>Current Inventory vs Reorder Point</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={invBars} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" stroke="rgba(244,244,247,0.55)" fontSize={10} interval={0} angle={-25} textAnchor="end" height={62} />
              <YAxis stroke="rgba(244,244,247,0.55)" fontSize={11} />
              <Tooltip />
              <Legend />
              <Bar dataKey="current" name="Current Stock" fill="#7f5af0" radius={[4, 4, 0, 0]} />
              <Bar dataKey="reorder" name="Reorder Point" fill="#ffb86b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Demand Distribution by Category</h3>
          <div className="chart-with-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={donutData} dataKey="revenue" nameKey="category" cx="50%" cy="50%" outerRadius={100} innerRadius={62} paddingAngle={2}>
                  {donutData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <div className="big">{formatCurrency(donutTotal)}</div>
              <div className="small">Total Revenue</div>
            </div>
          </div>
        </div>
      </div>

      {/* ---- Bottom data grid ---- */}
      <div className="card">
        <div className="between" style={{ marginBottom: '0.75rem' }}>
          <h3 style={{ margin: 0 }}>Demand &amp; Reorder Plan</h3>
          <span className="muted" style={{ fontSize: '0.8rem' }}>{gridRows.length} products{cat !== 'All' ? ` · ${cat}` : ''}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Product Name</th>
                <th>Category</th>
                <th style={{ textAlign: 'right' }}>Predicted Demand (30d)</th>
                <th style={{ textAlign: 'right' }}>Recommended Order Qty</th>
                <th>Risk Level</th>
                <th>Action Status</th>
              </tr>
            </thead>
            <tbody>
              {gridRows.map((r) => (
                <tr key={r.id}>
                  <td className="truncate" style={{ maxWidth: 220 }}>{r.name}</td>
                  <td>{r.category}</td>
                  <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(r.predicted)}</td>
                  <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(r.recommended)}</td>
                  <td><span className={`badge ${r.riskCls}`}>{r.risk}</span></td>
                  <td>{r.action}</td>
                </tr>
              ))}
              {!gridRows.length && (
                <tr><td colSpan={6}><div className="empty-state">No products in this category</div></td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
