import { useSystemStore } from '../../store/useSystemStore'
import { RESOURCE_STATUS_COLORS } from '../../config'
import { TYPE_EMOJI } from '../map/mapIcons'

const STATUS_LABEL = {
  available:       'Available',
  dispatched:      'Dispatched',
  en_route:        'En Route',
  on_scene:        'On Scene',
  returning:       'Returning',
  out_of_service:  'OOS',
}

export default function ResourceCard({ resource }) {
  const activeRoute = useSystemStore((s) => s.activeRoutes[resource.id])
  const dispatchCount = useSystemStore((s) => s.resourceDispatchCounts[resource.id] || 0)
  const nodeById = useSystemStore((s) => s.nodeById)

  const destNode = activeRoute?.to_node_id ? nodeById[activeRoute.to_node_id] : null
  const destName = destNode?.name || activeRoute?.to_node_id || null

  const color = RESOURCE_STATUS_COLORS[resource.status] || '#64748b'
  const emoji = TYPE_EMOJI[resource.resource_type] || '🚐'
  const label = STATUS_LABEL[resource.status] || resource.status

  // Progress bar for dispatched vehicles
  let progress = null
  if (activeRoute && activeRoute.etaSec > 0) {
    const elapsed = (Date.now() - activeRoute.startedAt) / 1000
    progress = Math.min(100, (elapsed / activeRoute.etaSec) * 100)
  }

  return (
    <div
      className="bg-slate-800 border border-slate-700 rounded p-2 flex flex-col gap-1"
      style={{ borderLeftWidth: 3, borderLeftColor: color }}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-base">{emoji}</span>
        <span className="text-xs font-semibold text-slate-200 truncate flex-1">{resource.call_sign}</span>
        {dispatchCount > 0 && (
          <span className="text-[9px] text-slate-500">×{dispatchCount}</span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[10px] font-medium" style={{ color }}>{label}</span>
        {activeRoute?.was_reassigned_from && (
          <span className="text-[9px] text-orange-400">↺</span>
        )}
      </div>

      {destName && (
        <div className="text-[10px] text-sky-400 truncate">→ {destName}</div>
      )}

      {progress !== null && (
        <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${progress}%`, background: color }}
          />
        </div>
      )}
    </div>
  )
}
