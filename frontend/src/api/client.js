import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const STORAGE_KEY = 'retail_forecast_auth'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for LSTM training
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT bearer token on every request
api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const { access_token } = JSON.parse(raw)
      if (access_token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${access_token}`
      }
    }
  } catch { /* ignore */ }
  return config
})

// Single, global 401 handler: drop the session and bounce to /login
let _on401 = null
export function onUnauthorized(cb) { _on401 = cb }

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && _on401) {
      _on401()
    }
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(typeof msg === 'string' ? msg : JSON.stringify(msg)))
  }
)

export const endpoints = {
  // Auth
  login: (username, password) => {
    const body = new URLSearchParams()
    body.append('username', username)
    body.append('password', password)
    return api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(r => r.data)
  },
  register: (payload) => api.post('/auth/register', payload).then(r => r.data),
  me: () => api.get('/auth/me').then(r => r.data),
  refresh: (refresh_token) => api.post(`/auth/refresh?refresh_token=${encodeURIComponent(refresh_token)}`).then(r => r.data),
  changePassword: (old_password, new_password) => api.post('/auth/change-password', null, { params: { old_password, new_password } }).then(r => r.data),

  // Products
  listProducts: () => api.get('/products').then(r => r.data),
  getProduct: (id) => api.get(`/products/${id}`).then(r => r.data),
  createProduct: (data) => api.post('/products', data).then(r => r.data),
  deleteProduct: (id) => api.delete(`/products/${id}`).then(r => r.data),

  // Sales
  listSales: (params) => api.get('/sales', { params }).then(r => r.data),
  importSalesCSV: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/sales/import-csv', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
  },

  // Forecast
  runForecast: (data) => api.post('/forecast/run', data).then(r => r.data),
  compareModels: (data) => api.post('/forecast/compare', data).then(r => r.data),
  getForecastHistory: (pid) => api.get(`/forecast/history/${pid}`).then(r => r.data),
  getSeasonal: (pid) => api.get(`/forecast/seasonal/${pid}`).then(r => r.data),
  listModels: () => api.get('/forecast/models').then(r => r.data),

  // Inventory
  listInventory: () => api.get('/inventory').then(r => r.data),
  updateStock: (pid, stock) => api.put(`/inventory/${pid}`, { current_stock: stock }).then(r => r.data),
  recomputeInventory: () => api.post('/inventory/recompute').then(r => r.data),

  // Reports
  generateReport: (data) => api.post('/reports/generate', data).then(r => r.data),
  listReports: () => api.get('/reports/list').then(r => r.data),
  // Authenticated download: a plain <a href> can't send the JWT header, so the
  // secured /reports/download endpoint returns 401. Fetch the file as a blob
  // (token attached by the request interceptor) and save it client-side.
  downloadReport: async (id) => {
    const res = await api.get(`/reports/download/${id}`, { responseType: 'blob' })
    const cd = res.headers['content-disposition'] || ''
    const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd)
    const filename = match ? decodeURIComponent(match[1]) : `report_${id}`
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    return filename
  },

  // Dashboard
  dashboardSummary: () => api.get('/dashboard/summary').then(r => r.data),
  revenueTrend: (days = 30) => api.get(`/dashboard/revenue-trend`, { params: { days } }).then(r => r.data),
  categoryBreakdown: () => api.get('/dashboard/category-breakdown').then(r => r.data),
  demandTrend: (days = 30) => api.get('/dashboard/demand-trend', { params: { days } }).then(r => r.data),
}

export default api
