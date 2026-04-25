import { useState } from 'react'
import { Play, Square, RotateCcw } from 'lucide-react'
import { api } from '../../api/client'
import { useSystemStore } from '../../store/useSystemStore'
import { SCENARIO_OPTIONS } from '../../config'

export default function ScenarioControls() {
  const simulation = useSystemStore((s) => s.simulation)
  const setSimulation = useSystemStore((s) => s.setSimulation)
  const setResources = useSystemStore((s) => s.setResources)
  const resetAll = useSystemStore((s) => s.resetAll)

  const [scenario, setScenario] = useState('earthquake_chaos')
  const [speed, setSpeed] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const running = simulation?.is_running
  const simStats = simulation?.stats || {}

  async function handleStart() {
    setError(null)
    setLoading(true)
    try {
      const result = await api.startScenario(scenario, speed)
      setSimulation(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleStop() {
    setLoading(true)
    try {
      const result = await api.stopSimulation()
      setSimulation(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleReset() {
    setLoading(true)
    setError(null)
    try {
      await api.resetSimulation()
      resetAll()
      const resources = await api.getResources()
      setResources(resources)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-3 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Scenario</span>
        {running && simStats.scenario_name && (
          <span className="text-xs text-amber-400 ml-1">
            ▶ {simStats.scenario_name} ({simStats.calls_processed || 0} processed)
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <select
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          disabled={running || loading}
          className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-xs text-slate-200 disabled:opacity-40"
        >
          {SCENARIO_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>

        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-500">×</span>
          <select
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))}
            disabled={running || loading}
            className="bg-slate-800 border border-slate-600 rounded px-1.5 py-1.5 text-xs text-slate-200 disabled:opacity-40 w-16"
          >
            <option value={1}>1x</option>
            <option value={5}>5x</option>
            <option value={10}>10x</option>
            <option value={20}>20x</option>
            <option value={50}>50x</option>
          </select>
        </div>
      </div>

      <div className="flex gap-2">
        {!running ? (
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex items-center gap-1.5 bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white text-xs font-semibold px-3 py-1.5 rounded transition-colors"
          >
            <Play size={12} /> Start
          </button>
        ) : (
          <button
            onClick={handleStop}
            disabled={loading}
            className="flex items-center gap-1.5 bg-red-700 hover:bg-red-600 disabled:opacity-40 text-white text-xs font-semibold px-3 py-1.5 rounded transition-colors"
          >
            <Square size={12} /> Stop
          </button>
        )}

        <button
          onClick={handleReset}
          disabled={loading}
          className="flex items-center gap-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 text-xs font-semibold px-3 py-1.5 rounded transition-colors"
        >
          <RotateCcw size={12} /> Reset
        </button>
      </div>

      {error && (
        <p className="text-[10px] text-red-400 truncate" title={error}>{error}</p>
      )}
    </div>
  )
}
