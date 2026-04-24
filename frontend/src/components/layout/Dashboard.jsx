import { useEffect } from 'react'
import { useLiveConnection } from '../../hooks/useLiveConnection'
import StatsBar from '../stats/StatsBar'
import CityMap from '../map/CityMap'
import IncidentFeed from '../incidents/IncidentFeed'
import DecisionInspector from '../decisions/DecisionInspector'
import ResourcePanel from '../resources/ResourcePanel'
import ScenarioControls from '../controls/ScenarioControls'
import ManualCallInput from '../controls/ManualCallInput'
import SystemErrorToast from './SystemErrorToast'
import { api } from '../../api/client'

const CRITICAL_TRANSCRIPT = 'bhai fire at CP, 3 log phase hai andar, log phanse hain'
const MEDIUM_TRANSCRIPT = 'accident at Saket, 2 cars crashed, one person has back pain'

export default function Dashboard() {
  useLiveConnection()

  useEffect(() => {
    function handleKey(e) {
      if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return
      if (e.key === 'c' || e.key === 'C') {
        api.ingestCall(CRITICAL_TRANSCRIPT).catch(() => {})
      } else if (e.key === 'm' || e.key === 'M') {
        api.ingestCall(MEDIUM_TRANSCRIPT).catch(() => {})
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  return (
    <div className="h-full flex flex-col bg-slate-950 overflow-hidden">
      <SystemErrorToast />
      {/* Row 1: Stats bar */}
      <StatsBar />

      {/* Row 2: Main 3-column grid */}
      <div className="flex-1 min-h-0 flex">
        {/* Left: Live call feed */}
        <div className="w-72 shrink-0 flex flex-col min-h-0 border-r border-slate-800">
          <IncidentFeed />
        </div>

        {/* Centre: Map */}
        <div className="flex-1 min-w-0 min-h-0">
          <CityMap />
        </div>

        {/* Right: Decision inspector + fleet */}
        <div className="w-80 shrink-0 flex flex-col min-h-0 border-l border-slate-800">
          <DecisionInspector />
          <ResourcePanel />
        </div>
      </div>

      {/* Row 3: Controls bar */}
      <div className="shrink-0 border-t border-slate-800 bg-slate-900">
        <div className="flex divide-x divide-slate-800">
          <div className="flex-1">
            <ScenarioControls />
          </div>
          <div className="flex-1">
            <ManualCallInput />
          </div>
        </div>
      </div>
    </div>
  )
}
