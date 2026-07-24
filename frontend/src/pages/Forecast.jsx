import { useState, useEffect } from 'react'
import { endpoints } from '../components/useApi'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { Play, GitCompare, Sparkles } from 'lucide-react'
import { formatNumber } from '../utils/format'
import { useToast } from '../components/ToastContext'
import ProgressBar from '../components/ProgressBar'

const MODEL_COLORS = { prophet: '#7f5af0', xgboost: '#2cb1bc', lstm: '#ff6ec7' }
const COMPARE_MODELS = ['prophet', 'xgboost', 'lstm']

// Smoothly "creep" a progress value from `from` toward `to` while a request is
// in flight (we can't know true % of a single model, so we ease asymptotically).
// Returns a stop() function that clears the interval.
function startCreep(from, to, setter) {
  let cur = from
  setter(cur)
  const id = setInterval(() => {
    cur += (to - cur) * 0.09
    if (cur > to - 0.4) cur = to - 0.4
    setter(Math.round(cur * 10) / 10)
  }, 350)
  return () => clearInterval(id)
}

export default function Forecast() {
  const [products, setProducts] = useState([])
  const [productId, setProductId] = useState('')
  const [model, setModel] = useState('prophet')
  const [horizon, setHorizon] = useState(30)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [compareResult, setCompareResult] = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [compareProgress, setCompareProgress] = useState(0)
  const [compareSteps, setCompareSteps] = useState([])
  const toast = useToast()

  useEffect(() => {
    endpoints.listProducts()
      .then((p) => { setProducts(p); if (p.length && !productId) setProductId(p[0].id) })
      .catch((e) => { setError(e.message); toast.error(e.message) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const runForecast = async () => {
    setLoading(true); setError(null); setResult(null); setCompareResult(null)
    const stop = startCreep(0, model === 'lstm' ? 88 : 94, setProgress)
    try {
      const r = await endpoints.runForecast({ product_id: Number(productId), model_name: model, horizon_days: horizon })
      stop(); setProgress(100)
      setResult(r)
      toast.success(`${model.toUpperCase()} forecast complete — MAPE ${r.metrics.mape}%`)
    } catch (e) {
      stop(); setError(e.message); toast.error(e.message)
    } finally {
      setTimeout(() => setProgress(0), 600)
      setLoading(false)
    }
  }

  // Run each model sequentially via the fast single-forecast endpoint so we can
  // show real per-model progress and avoid the long single /compare request
  // timing out. Best model = lowest RMSE among the ones that succeeded.
  const compareModels = async () => {
    setCompareLoading(true); setError(null); setCompareResult(null); setCompareProgress(0)
    setCompareSteps(COMPARE_MODELS.map((m) => ({ key: m, label: m, status: 'pending' })))
    const results = {}
    try {
      for (let i = 0; i < COMPARE_MODELS.length; i++) {
        const m = COMPARE_MODELS[i]
        setCompareSteps((prev) => prev.map((s) => (s.key === m ? { ...s, status: 'active' } : s)))
        const base = (i / COMPARE_MODELS.length) * 100
        const target = ((i + 1) / COMPARE_MODELS.length) * 100
        const stop = startCreep(base, target, setCompareProgress)
        try {
          const r = await endpoints.runForecast({ product_id: Number(productId), model_name: m, horizon_days: horizon })
          const total = (r.forecasts || []).reduce((sum, f) => sum + (f.predicted_quantity || 0), 0)
          results[m] = { metrics: r.metrics, total_predicted: Math.round(total) }
        } catch (e) {
          results[m] = { metrics: null, total_predicted: null, error: e.message }
          toast.error(`${m.toUpperCase()} failed: ${e.message}`)
        } finally {
          stop(); setCompareProgress(target)
          setCompareSteps((prev) => prev.map((s) => (s.key === m ? { ...s, status: 'done' } : s)))
        }
      }
      let best = null; let bestRmse = Infinity
      for (const [m, r] of Object.entries(results)) {
        const rmse = r.metrics?.rmse
        if (rmse != null && rmse < bestRmse) { bestRmse = rmse; best = m }
      }
      setCompareResult({ results, best_model: best })
      toast.success(best ? `Best model: ${best} (lowest RMSE)` : 'Comparison finished — no model succeeded')
    } catch (e) {
      setError(e.message); toast.error(e.message)
    } finally {
      setTimeout(() => setCompareProgress(0), 800)
      setCompareLoading(false)
    }
  }

  const chartData = (result?.forecasts || []).map((f) => ({
    date: f.forecast_date,
    predicted: f.predicted_quantity,
    lower: f.lower_bound,
    upper: f.upper_bound,
  }))
  const accent = MODEL_COLORS[result?.model_name] || '#7f5af0'

  return (
    <div>
      <div className="card">
        <div className="form-row">
          <div className="form-group">
            <label>Product</label>
            <select value={productId} onChange={(e) => setProductId(e.target.value)}>
              <option value="">Select product…</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Model</label>
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="prophet">Prophet (additive trend + seasonality)</option>
              <option value="xgboost">XGBoost (gradient boosting)</option>
              <option value="lstm">LSTM (deep learning)</option>
            </select>
          </div>
          <div className="form-group" style={{ maxWidth: 160 }}>
            <label>Horizon (days)</label>
            <input type="number" min={1} max={365} value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} />
          </div>
          <button onClick={runForecast} disabled={!productId || loading}>
            <Play size={14} />
            {loading ? 'Forecasting…' : 'Run Forecast'}
          </button>
          <button className="secondary" onClick={compareModels} disabled={!productId || compareLoading}>
            <GitCompare size={14} />
            {compareLoading ? 'Comparing…' : 'Compare All Models'}
          </button>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {loading && (
          <ProgressBar
            value={progress}
            label={`Forecasting with ${model.toUpperCase()}${model === 'lstm' ? ' — deep learning, this can take 1–2 min' : ''}…`}
          />
        )}
        {compareLoading && (
          <ProgressBar value={compareProgress} label="Comparing all models…" steps={compareSteps} />
        )}
      </div>

      {result && (
        <>
          <div className="grid grid-3">
            <div className="stat-card">
              <div className="label">MAE</div>
              <div className="value">{formatNumber(result.metrics?.mae || 0)}</div>
              <div className="delta">Mean Absolute Error</div>
            </div>
            <div className="stat-card">
              <div className="label">RMSE</div>
              <div className="value">{formatNumber(result.metrics?.rmse || 0)}</div>
              <div className="delta">Root Mean Squared Error</div>
            </div>
            <div className="stat-card">
              <div className="label">MAPE (%)</div>
              <div className="value">{formatNumber(result.metrics?.mape || 0)}</div>
              <div className="delta">Mean Absolute % Error</div>
            </div>
          </div>

          <div className="card">
            <h3>Forecast — {result.model_name} · next {result.horizon_days} days</h3>
            <ResponsiveContainer width="100%" height={360}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="g-pred" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={accent} stopOpacity={0.6} />
                    <stop offset="100%" stopColor={accent} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" stroke="rgba(244,244,247,0.55)" fontSize={11} />
                <YAxis stroke="rgba(244,244,247,0.55)" fontSize={11} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="upper" stroke={accent} strokeOpacity={0.3} fill="transparent" name="Upper bound" />
                <Area type="monotone" dataKey="predicted" stroke={accent} strokeWidth={2.5} fill="url(#g-pred)" name="Predicted" />
                <Area type="monotone" dataKey="lower" stroke={accent} strokeOpacity={0.3} fill="transparent" name="Lower bound" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3>Forecast Table</h3>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Date</th><th style={{ textAlign: 'right' }}>Predicted</th><th style={{ textAlign: 'right' }}>Lower</th><th style={{ textAlign: 'right' }}>Upper</th></tr></thead>
                <tbody>
                  {result.forecasts.map((f, i) => (
                    <tr key={i}>
                      <td className="mono">{f.forecast_date}</td>
                      <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(f.predicted_quantity)}</td>
                      <td className="mono muted" style={{ textAlign: 'right' }}>{formatNumber(f.lower_bound)}</td>
                      <td className="mono muted" style={{ textAlign: 'right' }}>{formatNumber(f.upper_bound)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {compareResult && (
        <div className="card">
          <h3><Sparkles size={16} style={{ marginRight: 6, verticalAlign: 'middle', color: '#ffb86b' }} /> Model Comparison</h3>
          {compareResult.best_model && (
            <div className="alert alert-success">
              <strong>Recommended model:</strong> {compareResult.best_model} (lowest RMSE)
            </div>
          )}
          <div className="table-wrap">
            <table>
              <thead><tr><th>Model</th><th style={{ textAlign: 'right' }}>MAE</th><th style={{ textAlign: 'right' }}>RMSE</th><th style={{ textAlign: 'right' }}>MAPE (%)</th><th style={{ textAlign: 'right' }}>Total Predicted (next {horizon}d)</th></tr></thead>
              <tbody>
                {Object.entries(compareResult.results || {}).map(([m, r]) => (
                  <tr key={m} style={m === compareResult.best_model ? { background: 'rgba(127, 90, 240, 0.10)' } : undefined}>
                    <td><span className="badge" style={{ background: `${MODEL_COLORS[m]}22`, color: MODEL_COLORS[m] }}>{m}</span></td>
                    <td className="mono" style={{ textAlign: 'right' }}>{r.metrics?.mae ?? '—'}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{r.metrics?.rmse ?? '—'}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{r.metrics?.mape ?? '—'}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{r.total_predicted ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
