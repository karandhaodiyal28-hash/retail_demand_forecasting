import { useState, useEffect } from 'react'
import { endpoints } from '../components/useApi'
import { Plus, Trash2, Package, Save, X } from 'lucide-react'
import { useToast } from '../components/ToastContext'

const EMPTY = { sku: '', name: '', category: '', unit_cost: 0, unit_price: 0, lead_time_days: 5 }

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY)
  const toast = useToast()

  const load = async () => {
    setLoading(true); setError(null)
    try { setProducts(await endpoints.listProducts()) }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const submit = async () => {
    try {
      await endpoints.createProduct(form)
      toast.success(`Product ${form.sku} created`)
      setForm(EMPTY); setShowForm(false); load()
    } catch (e) { setError(e.message); toast.error(e.message) }
  }

  const remove = async (id, sku) => {
    if (!confirm(`Delete product ${sku}?`)) return
    try { await endpoints.deleteProduct(id); toast.success('Product deleted'); load() }
    catch (e) { toast.error(e.message) }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Products</h2>
          <p>Manage the product catalogue (SKU master)</p>
        </div>
        <button onClick={() => setShowForm((s) => !s)}>
          {showForm ? <X size={14} /> : <Plus size={14} />}
          {showForm ? 'Cancel' : 'Add Product'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <div className="card">
          <h3>New Product</h3>
          <div className="form-row">
            <div className="form-group"><label>SKU</label><input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="e.g. OIL-003" /></div>
            <div className="form-group"><label>Name</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Olive Oil 1L" /></div>
            <div className="form-group"><label>Category</label><input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="e.g. Grocery" /></div>
            <div className="form-group"><label>Unit Cost (₹)</label><input type="number" min={0} value={form.unit_cost} onChange={(e) => setForm({ ...form, unit_cost: Number(e.target.value) })} /></div>
            <div className="form-group"><label>Unit Price (₹)</label><input type="number" min={0} value={form.unit_price} onChange={(e) => setForm({ ...form, unit_price: Number(e.target.value) })} /></div>
            <div className="form-group"><label>Lead Time (days)</label><input type="number" min={0} max={365} value={form.lead_time_days} onChange={(e) => setForm({ ...form, lead_time_days: Number(e.target.value) })} /></div>
            <button onClick={submit} style={{ alignSelf: 'flex-end' }}><Save size={14} /> Save Product</button>
          </div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading-overlay"><span className="spinner" /> Loading products…</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>SKU</th><th>Name</th><th>Category</th>
                  <th style={{ textAlign: 'right' }}>Cost</th>
                  <th style={{ textAlign: 'right' }}>Price</th>
                  <th style={{ textAlign: 'right' }}>Lead Time</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.sku}</td>
                    <td className="truncate" style={{ maxWidth: 280 }}>{p.name}</td>
                    <td>{p.category || <span className="muted">—</span>}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>₹{p.unit_cost}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>₹{p.unit_price}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{p.lead_time_days}d</td>
                    <td>
                      <button className="secondary" onClick={() => remove(p.id, p.sku)} style={{ padding: '0.4rem 0.6rem' }} title="Delete">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {!products.length && (
                  <tr><td colSpan={7}><div className="empty-state"><Package size={20} /><br />No products yet</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
