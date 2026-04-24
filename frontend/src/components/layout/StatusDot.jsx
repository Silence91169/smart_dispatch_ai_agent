import { useSystemStore } from '../../store/useSystemStore'

const DOT = {
  connected:    'bg-green-400',
  connecting:   'bg-yellow-400 animate-pulse',
  disconnected: 'bg-slate-500',
  error:        'bg-red-500 animate-pulse',
  failed:       'bg-red-700',
}

export default function StatusDot() {
  const status = useSystemStore((s) => s.connectionStatus)
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${DOT[status] || 'bg-slate-500'}`} title={status} />
}
