import { useState, useEffect } from 'react'
import { endpoints } from '../components/useApi'
import { Download, FileText, FileJson, FileSpreadsheet, Clock } from 'lucide-react'
import { useToast } from '../components/ToastContext'

const TYPES = [
  { value: 'forecast',  label: 'Forecast' },
  { value: 'inventory', label: 'Inventory (all products)' },
  { value: 'seasonal',  label: 'Seasonal Analysis' },
]

export default function Reports() {
  const [products, setProducts] = useState([])
  const [reports, setReports] = useState([])
  const [reportType, setReportType] = useState('forecast')
  const [productId, setProductId] = useState('')
  const [format, setFormat] = useState('json')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastReport, setLastReport] = useState(null)
  const toast = useToast()

  const load = async () => {
    try {
      const [p, r] = await Promise.all([endpoints.listProducts(), endpoints.listReports()])
      setProducts(p); setReports(r)
      if (p.length && !productId) setProductId(p[0].id)
    } catch (e) { setError(e.message); toast.error(e.message) }
  }
  useEffect(() => { load() }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  const generate = async () => {
    setLoading(true); setError(null); setLastReport(null)
    try {
      if (reportType !== 'inventory' && !productId) {
        const msg = 'Please select a product for forecast/seasonal reports'
        setError(msg); toast.error(msg); setLoading(false); return
      }
      const body = { report_type: reportType, format }
      if (reportType !== 'inventory') body.product_id = Number(productId)
      const r = await endpoints.generateReport(body)
      setLastReport(r)
      toast.success(`Report generated (${(r.size_bytes / 1024).toFixed(1)} KB)`)
      load()
    } catch (e) { setError(e.message); toast.error(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div className="card">
        <h3><FileText size={16} style={{ marginRight: 6, verticalAlign: 'middle', color: '#7f5af0' }} /> Generate New Report</h3>
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: 220 }}>
            <label>Report Type</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
              {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          {reportType !== 'inventory' && (
            <div className="form-group" style={{ maxWidth: 320 }}>
              <label>Product</label>
              <select value={productId} onChange={(e) => setProductId(e.target.value)}>
                <option value="">Select product…</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
              </select>
            </div>
          )}
          <div className="form-group" style={{ maxWidth: 140 }}>
            <label>Format</label>
            <select value={format} onChange={(e) => setFormat(e.target.value)}>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <button onClick={generate} disabled={loading}>
            <FileText size={14} />
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {lastReport && (
          <div className="alert alert-success">
            Report #{lastReport.report_id} generated · {' '}
            <a href={endpoints.downloadReportUrl(lastReport.report_id)} target="_blank" rel="noreferrer">
              <Download size={12} style={{ verticalAlign: 'middle' }} /> Download {lastReport.format.toUpperCase()}
            </a>
          </div>
        )}
      </div>

      <div className="card">
        <h3><Clock size={16} style={{ marginRight: 6, verticalAlign: 'middle', color: '#2cb1bc' }} /> Recent Reports</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Type</th><th>Product</th><th>Format</th>
                <th>Created</th><th>Size</th><th></th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id}>
                  <td className="mono">#{r.id}</td>
                  <td><span className="badge badge-ok">{r.report_type}</span></td>
                  <td>{r.product_id ? `#${r.product_id}` : <span className="muted">—</span>}</td>
                  <td>
                    {r.format === 'json'
                      ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><FileJson size={14} /> JSON</span>
                      : <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><FileSpreadsheet size={14} /> CSV</span>}
                  </td>
                  <td className="mono">{new Date(r.created_at).toLocaleString('en-IN')}</td>
                  <td className="mono muted">{(r.file_path && (r.file_path.length)) || '—'}</td>
                  <td>
                    <a href={endpoints.downloadReportUrl(r.id)} target="_blank" rel="noreferrer" title="Download">
                      <button className="secondary" style={{ padding: '0.4rem 0.6rem' }}><Download size={14} /></button>
                    </a>
                  </td>
                </tr>
              ))}
              {!reports.length && (
                <tr><td colSpan={7}><div className="empty-state"><FileText size={20} /><br />No reports generated yet</div></td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
