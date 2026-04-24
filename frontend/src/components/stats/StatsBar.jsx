import { useState } from 'react'
import { useSystemStore } from '../../store/useSystemStore'
import { api } from '../../api/client'

function Stat({ emoji, label, value, accent }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1">
      <span className="text-sm">{emoji}</span>
      <div className="flex flex-col">
        <span className={`text-sm font-bold leading-none ${accent || 'text-slate-100'}`}>{value}</span>
        <span className="text-[9px] text-slate-500 leading-none mt-0.5">{label}</span>
      </div>
    </div>
  )
}

function Divider() {
  return <div className="w-px h-6 bg-slate-700 self-center" />
}

export default function StatsBar() {
  const counters = useSystemStore((s) => s.counters)
  const stats = useSystemStore((s) => s.stats)
  const simulation = useSystemStore((s) => s.simulation)
  const connectionStatus = useSystemStore((s) => s.connectionStatus)
  const showSystemError = useSystemStore((s) => s.showSystemError)

  const [evalState, setEvalState] = useState('idle')  // idle | running | done
  const [evalResult, setEvalResult] = useState(null)

  async function handleRunEval() {
    setEvalState('running')
    setEvalResult(null)
    try {
      const result = await api.runEval(10)
      setEvalResult(result)
      setEvalState('done')
      setTimeout(() => setEvalState('idle'), 30000)
    } catch (e) {
      showSystemError(`Eval failed: ${e.message.slice(0, 80)}`)
      setEvalState('idle')
    }
  }

  const dupRate = counters.totalCalls > 0
    ? ` (${((counters.totalDuplicates / counters.totalCalls) * 100).toFixed(0)}%)`
    : ''

  const dotColor = {
    connected:    'bg-green-400',
    connecting:   'bg-yellow-400 animate-pulse',
    disconnected: 'bg-slate-500',
    error:        'bg-red-500 animate-pulse',
    failed:       'bg-red-700',
  }[connectionStatus] || 'bg-slate-500'

  return (
    <div className="flex items-center bg-slate-900 border-b border-slate-700 shrink-0 overflow-x-auto">
      {/* Branding */}
      <div className="px-3 py-1.5 flex items-center gap-2 border-r border-slate-700 shrink-0">
        <span className="text-base">🚨</span>
        <span className="text-xs font-bold text-slate-200 whitespace-nowrap">Delhi 112</span>
      </div>

      {/* Counters */}
      <Stat emoji="📞" label="Calls" value={counters.totalCalls} />
      <Divider />
      <Stat emoji="🔁" label={`Duplicates${dupRate}`} value={counters.totalDuplicates} accent="text-purple-400" />
      <Divider />
      <Stat emoji="🚨" label="Incidents" value={counters.totalIncidents} accent="text-red-400" />
      <Divider />
      <Stat emoji="🚑" label="Dispatches" value={counters.totalDispatches} accent="text-amber-400" />
      <Divider />
      <Stat emoji="↺" label="Re-routes" value={counters.totalReassignments} accent="text-orange-400" />
      <Divider />
      <Stat
        emoji="⚠️"
        label="Unfulfilled"
        value={counters.unfulfilledCount}
        accent={counters.unfulfilledCount > 0 ? 'text-red-500' : 'text-slate-400'}
      />

      {/* DB counts from REST (more authoritative) */}
      {stats && (
        <>
          <Divider />
          <Stat emoji="📊" label="DB Incidents" value={stats.incidents_total} />
          <Divider />
          <Stat
            emoji="🚒"
            label="Available"
            value={`${stats.resources_available}/${stats.resources_total}`}
            accent="text-green-400"
          />
        </>
      )}

      {/* Sim status */}
      {simulation?.is_running && (
        <>
          <Divider />
          <div className="flex items-center gap-1.5 px-3 py-1">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-[10px] text-green-400 font-semibold whitespace-nowrap">
              LIVE · {simulation.stats?.scenario_name || ''}
            </span>
          </div>
        </>
      )}

      {/* Run Eval button */}
      <div className="ml-auto flex items-center gap-2 px-3 border-l border-slate-700">
        <button
          onClick={handleRunEval}
          disabled={evalState === 'running'}
          title="Run accuracy eval on 10 golden cases (~30s)"
          className={`text-[9px] font-semibold px-2 py-0.5 rounded border transition-colors
            ${evalState === 'running'
              ? 'bg-slate-800 border-slate-600 text-slate-500 cursor-wait'
              : evalState === 'done'
              ? 'bg-emerald-900 border-emerald-600 text-emerald-300'
              : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-400'
            }`}
        >
          {evalState === 'running' ? '⏳ Eval…' : evalState === 'done' ? '✓ Eval done' : '📊 Run Eval'}
        </button>
        {evalResult && evalState === 'done' && (
          <span className="text-[9px] text-emerald-400 whitespace-nowrap">
            type {(evalResult.triage?.type_accuracy * 100).toFixed(0)}% ·
            sev {(evalResult.triage?.severity_accuracy * 100).toFixed(0)}% ·
            F1 {evalResult.dedup?.f1?.toFixed(2)}
          </span>
        )}
      </div>

      {/* Connection dot */}
      <div className="flex items-center gap-2 px-3 border-l border-slate-700">
        <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
        <span className="text-[10px] text-slate-500 capitalize">{connectionStatus}</span>
      </div>
    </div>
  )
}
