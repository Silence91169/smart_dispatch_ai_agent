import { SEVERITY_COLORS } from '../../config'

const BG = {
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/40',
  HIGH:     'bg-orange-500/20 text-orange-400 border-orange-500/40',
  MEDIUM:   'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  LOW:      'bg-blue-500/20 text-blue-400 border-blue-500/40',
}

export default function SeverityBadge({ severity, small = false }) {
  const cls = BG[severity] || 'bg-slate-500/20 text-slate-400 border-slate-500/40'
  return (
    <span
      className={`inline-flex items-center border rounded font-semibold uppercase tracking-wide ${cls} ${small ? 'text-[9px] px-1 py-px' : 'text-[10px] px-1.5 py-0.5'}`}
    >
      {severity || '?'}
    </span>
  )
}
