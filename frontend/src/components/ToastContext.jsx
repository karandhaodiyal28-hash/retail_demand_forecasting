import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle2, XCircle, Info, AlertTriangle } from 'lucide-react'

const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
}

let counter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const push = useCallback((message, type = 'info', timeout = 3500) => {
    const id = ++counter
    setToasts((cur) => [...cur, { id, message, type }])
    setTimeout(() => {
      setToasts((cur) => cur.filter((t) => t.id !== id))
    }, timeout)
  }, [])

  const api = {
    success: (m) => push(m, 'success'),
    error:   (m) => push(m, 'error', 5000),
    info:    (m) => push(m, 'info'),
    warning: (m) => push(m, 'warning'),
  }

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => {
          const Icon = ICONS[t.type] || Info
          return (
            <div key={t.id} className={`toast ${t.type}`}>
              <Icon size={16} />
              <span>{t.message}</span>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside ToastProvider')
  return ctx
}
