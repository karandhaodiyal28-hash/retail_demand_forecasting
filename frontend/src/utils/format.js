export const formatCurrency = (n) => {
  if (n == null || isNaN(n)) return '₹0'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n)
}

export const formatNumber = (n) => {
  if (n == null || isNaN(n)) return '0'
  return new Intl.NumberFormat('en-IN').format(n)
}

export const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const statusColor = (s) => ({
  OK: '#16a34a',
  LOW: '#eab308',
  REORDER: '#dc2626',
  OVERSTOCK: '#2563eb',
  ERROR: '#71717a',
}[s] || '#71717a')
