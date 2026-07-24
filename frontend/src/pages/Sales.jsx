import { useState, useEffect } from 'react'
import { endpoints } from '../components/useApi'
import { Upload, ShoppingCart, FileSpreadsheet } from 'lucide-react'
import { formatCurrency } from '../utils/format'
import { useToast } from '../components/ToastContext'

export default function Sales() {
  const [sales, setSales] = useState([])
  const [products, setProducts] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const toast = useToast()

  useEffect(() => {
    Promise.all([endpoints.listSales({ limit: 500 }), endpoints.listProducts()])
      .then(([s, p]) => { setSales(s); setProducts(p) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) { toast.error('File too large (max 10 MB)'); return }
    try {
      const r = await endpoints.importSalesCSV(file)
      toast.success(r.detail || 'Import complete')
      const s = await endpoints.listSales({ limit: 500 })
      setSales(s)
    } catch (err) { toast.error(err.message) }
    e.target.value = ''   // allow re-upload of same file
  }

  const filtered = filter ? sales.filter((s) => s.product_id === Number(filter)) : sales
  const pidToName = Object.fromEntries(products.map((p) => [p.id, p.name]))

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Sales Records</h2>
          <p>Daily sales history used as training input for forecasting models</p>
        </div>
        <label className="btn secondary" style={{ cursor: 'pointer' }}>
          <Upload size={14} /> Import CSV
          <input type="file" accept=".csv" hidden onChange={handleUpload} />
        </label>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: 360 }}>
            <label>Filter by product</label>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All products</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
            </select>
          </div>
          <div style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: '0.85rem', alignSelf: 'center' }}>
            Showing <strong style={{ color: 'var(--text)' }}>{filtered.length}</strong> of {sales.length} rows
          </div>
        </div>

        {loading ? (
          <div className="loading-overlay"><span className="spinner" /> Loading sales…</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Product</th><th style={{ textAlign: 'right' }}>Quantity</th><th style={{ textAlign: 'right' }}>Revenue</th></tr></thead>
              <tbody>
                {filtered.slice(0, 500).map((s, i) => (
                  <tr key={i}>
                    <td className="mono">{s.sale_date}</td>
                    <td className="truncate" style={{ maxWidth: 280 }}>{pidToName[s.product_id] || `#${s.product_id}`}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{s.quantity}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{formatCurrency(s.revenue)}</td>
                  </tr>
                ))}
                {!filtered.length && (
                  <tr><td colSpan={4}><div className="empty-state"><FileSpreadsheet size={20} /><br />No sales records</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
