import { useSystemStore } from '../../store/useSystemStore'
import SeverityBadge from '../incidents/SeverityBadge'
import ReasoningBubble from './ReasoningBubble'

export default function DecisionInspector() {
  const decisions = useSystemStore((s) => s.decisions)
  const selectedId = useSystemStore((s) => s.selectedIncidentId)
  const selectIncident = useSystemStore((s) => s.selectIncident)

  const decision = selectedId
    ? decisions.find((d) => d.incident_id === selectedId) || decisions[0]
    : decisions[0]

  return (
    <div className="flex flex-col bg-slate-900 border-b border-slate-700" style={{ maxHeight: '55%' }}>
      <div className="px-3 py-2 border-b border-slate-700 flex items-center gap-2 shrink-0">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Decision Inspector</span>
        {selectedId && (
          <button
            onClick={() => selectIncident(null)}
            className="ml-auto text-[10px] text-slate-500 hover:text-slate-300"
          >
            ✕ clear
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto scroll-thin p-3">
        {!decision ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 text-xs gap-2">
            <span className="text-2xl">🧠</span>
            <span>Waiting for dispatch…</span>
          </div>
        ) : (
          <div>
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <SeverityBadge severity={decision.severity} />
              <span className="text-xs font-semibold text-slate-200">{decision.incident_type}</span>
              <span className="text-[10px] text-slate-500 ml-auto">
                {decision.incident_id?.slice(-8)}
              </span>
            </div>

            {/* Location */}
            {decision.location_node_id && (
              <div className="text-[10px] text-slate-400 mb-2">
                📍 Node {decision.location_node_id}
              </div>
            )}

            {/* Assignments */}
            {decision.assignments?.length > 0 && (
              <div className="mb-2">
                <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-wide">Dispatched</div>
                <div className="space-y-1">
                  {decision.assignments.map((a, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className="font-medium text-amber-400">{a.call_sign}</span>
                      <span className="text-slate-500">{a.resource_type}</span>
                      <span className="ml-auto text-slate-400">
                        {a.travel_time_sec === 0 ? 'On-scene' : `${(a.travel_time_sec / 60).toFixed(1)} min`}
                      </span>
                      {a.was_reassigned_from && (
                        <span className="text-orange-400 text-[9px] font-bold">↺ RE-ROUTED</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Unfulfilled */}
            {decision.unfulfilled_resources?.length > 0 && (
              <div className="mb-2 text-[10px] text-red-400 bg-red-900/20 rounded px-2 py-1">
                ⚠️ Unfulfilled: {decision.unfulfilled_resources.join(', ')}
              </div>
            )}

            {/* LLM Reasoning */}
            <ReasoningBubble
              reasoning={decision.decision_reasoning || decision.fallback_reasoning}
              alternatives={decision.considered_alternatives || []}
            />
          </div>
        )}
      </div>
    </div>
  )
}
