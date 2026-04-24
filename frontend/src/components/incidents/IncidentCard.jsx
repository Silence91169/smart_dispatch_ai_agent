import SeverityBadge from './SeverityBadge'
import { useTimeAgo } from '../../hooks/useTimeAgo'

const STAGE_LABEL = {
  triage_pending:  { text: '⏳ Triaging…',   cls: 'text-slate-400' },
  dispatch_pending: { text: '📡 Dispatching…', cls: 'text-amber-400' },
  duplicate:       { text: '🔁 Duplicate',    cls: 'text-purple-400' },
  error:           { text: '❌ Error',         cls: 'text-red-400' },
}

export default function IncidentCard({ item }) {
  const ago = useTimeAgo(item.timestamp)
  const { triage, dispatch, stage, transcript, error } = item
  const stageInfo = STAGE_LABEL[stage] || { text: '✅ Dispatched', cls: 'text-green-400' }
  const severity = triage?.severity || null

  return (
    <div className="fade-in bg-slate-800 border border-slate-700 rounded-lg p-3 mb-2 text-sm">
      {/* Header row */}
      <div className="flex items-center gap-2 mb-1.5">
        {severity && <SeverityBadge severity={severity} small />}
        {triage?.incident_type && (
          <span className="text-xs font-medium text-slate-300">{triage.incident_type}</span>
        )}
        <span className={`ml-auto text-xs ${stageInfo.cls}`}>{stageInfo.text}</span>
        <span className="text-xs text-slate-500 ml-2">{ago}</span>
      </div>

      {/* Transcript */}
      <p className="text-slate-300 text-xs leading-relaxed mb-1.5 line-clamp-2">
        {transcript || '…'}
      </p>

      {/* Triage chips */}
      {triage && (
        <div className="flex flex-wrap gap-1 mb-1.5">
          {triage.location_raw && (
            <span className="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-px rounded">
              📍 {triage.location_raw}
            </span>
          )}
          {triage.is_duplicate && triage.duplicate_of_call_id && (
            <span className="text-[10px] bg-purple-900/50 text-purple-300 px-1.5 py-px rounded">
              ≡ dup of {triage.duplicate_of_call_id.slice(-6)}
            </span>
          )}
          {triage.processing_time_ms && (
            <span className="text-[10px] bg-slate-700 text-slate-400 px-1.5 py-px rounded">
              {(triage.processing_time_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      )}

      {/* Dispatch line */}
      {dispatch && dispatch.assignments?.length > 0 && (
        <div className="text-[10px] text-amber-400 flex flex-wrap gap-x-2">
          {dispatch.assignments.slice(0, 3).map((a, i) => (
            <span key={i}>
              {a.call_sign} → {(a.travel_time_sec / 60).toFixed(1)}min
            </span>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-[10px] text-red-400 mt-1 line-clamp-2 opacity-80">{error}</p>
      )}
    </div>
  )
}
