import { Check } from 'lucide-react'

/**
 * Animated progress bar with optional labelled steps.
 *
 * Props:
 *  - value:  0..100 percentage (required)
 *  - label:  heading text shown top-left (e.g. "Comparing models…")
 *  - steps:  optional array of { key, label, status } where status is
 *            'done' | 'active' | 'pending' — renders a pill row below the bar.
 */
export default function ProgressBar({ value = 0, label = 'Working…', steps = [] }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className="progress">
      <div className="progress-head">
        <span>{label}</span>
        <span className="pct">{pct}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      {steps.length > 0 && (
        <div className="progress-steps">
          {steps.map((s) => (
            <span key={s.key} className={`progress-step ${s.status}`}>
              {s.status === 'done' ? <Check size={12} /> : <span className="dot" />}
              {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
