import { useApi, endpoints } from '../components/useApi'
import { RefreshCw, Boxes, AlertCircle, CheckCircle2, TrendingDown, Package2 } from 'lucide-react'
import { formatNumber, statusColor } from '../utils/format'
import { useToast } from '../components/ToastContext'

const STATUS_META = {
  OK:        { icon: CheckCircle2, label: 'OK' },
  LOW:       { icon: TrendingDown, label: 'LOW' },
  REORDER:   { icon: AlertCircle,  label: 'REORDER' },
  OVERSTOCK: { icon: Package2,     label: 'OVERSTOCK' },
  ERROR:     { icon: AlertCircle,  label: 'ERROR' },
}

export default function Inventory() {
  const { data, loading, error, refetch } = useApi(endpoints.listInventory, [])
  const toast = useToast()

  const recompute = async () => {
    try {
      const r = await endpoints.recomputeInventory()
      toast.success(r.detail || 'Inventory recomputed')
      refetch()
    } catch (e) { toast.error(e.message) }
  }

  if (loading) return <div className="loading-overlay"><span className="spinner" /> Loading inventory…</div>
  if (error)   return <div className="alert alert-error">{error}</div>

  const summary = (data || []).reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Inventory Management</h2>
          <p>Stock levels, reorder points, and AI-driven replenishment recommendations</p>
        </div>
        <button className="secondary" onClick={recompute}>
          <RefreshCw size={14} /> Recompute
        </button>
      </div>

      <div className="grid grid-4">
        {Object.entries(STATUS_META).map(([status, meta]) => (
          <div className="stat-card" key={status}>
            <div className="icon-pill" style={{ color: statusColor(status), background: `${statusColor(status)}22` }}>
              <meta.icon size={20} />
            </div>
            <div className="label">{meta.label}</div>
            <div className="value" style={{ color: statusColor(status) }}>{summary[status] || 0}</div>
            <div className="delta muted">products in this state</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3><Boxes size={16} style={{ marginRight: 6, verticalAlign: 'middle', color: '#2cb1bc' }} /> Inventory Status — All Products</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>SKU</th><th>Product</th>
                <th style={{ textAlign: 'right' }}>Current Stock</th>
                <th style={{ textAlign: 'right' }}>Reorder Point</th>
                <th style={{ textAlign: 'right' }}>Safety Stock</th>
                <th style={{ textAlign: 'right' }}>Recommended Order</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {(data || []).map((r, i) => (
                <tr key={i}>
                  <td className="mono">{r.sku}</td>
                  <td className="truncate" style={{ maxWidth: 220 }}>{r.name}</td>
                  <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(r.current_stock)}</td>
                  <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(r.reorder_point)}</td>
                  <td className="mono" style={{ textAlign: 'right' }}>{formatNumber(r.safety_stock)}</td>
                  <td className="mono" style={{ textAlign: 'right', fontWeight: 700 }}>{formatNumber(r.recommended_order_qty)}</td>
                  <td><span className="badge" style={{ background: `${statusColor(r.status)}22`, color: statusColor(r.status) }}>{r.status}</span></td>
                  <td className="muted" style={{ fontSize: '0.78rem' }}>{r.notes}</td>
                </tr>
              ))}
              {!data?.length && <tr><td colSpan={8}><div className="empty-state">No inventory data</div></td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
