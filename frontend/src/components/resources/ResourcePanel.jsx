import { useSystemStore } from '../../store/useSystemStore'
import ResourceCard from './ResourceCard'

const STATUS_ORDER = { en_route: 0, dispatched: 0, on_scene: 1, returning: 2, available: 3, out_of_service: 4 }

export default function ResourcePanel() {
  const resources = useSystemStore((s) => s.resources)
  const sorted = Object.values(resources).sort(
    (a, b) => (STATUS_ORDER[a.status] ?? 5) - (STATUS_ORDER[b.status] ?? 5)
  )

  const available = sorted.filter((r) => r.status === 'available').length
  const total = sorted.length

  return (
    <div className="flex flex-col border-t border-slate-700 min-h-0 flex-1">
      <div className="px-3 py-1.5 border-b border-slate-700 flex items-center gap-2 shrink-0">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fleet</span>
        <span className="ml-auto text-xs text-slate-500">
          <span className="text-green-400 font-semibold">{available}</span>/{total} available
        </span>
      </div>
      <div className="flex-1 overflow-y-auto scroll-thin p-2">
        {sorted.length === 0 ? (
          <div className="text-slate-600 text-xs text-center mt-4">Loading fleet…</div>
        ) : (
          <div className="grid grid-cols-2 gap-1.5">
            {sorted.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
