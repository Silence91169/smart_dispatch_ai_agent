import { useSystemStore } from '../../store/useSystemStore'
import IncidentCard from './IncidentCard'

export default function IncidentFeed() {
  const feed = useSystemStore((s) => s.feed)

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-700">
      <div className="px-3 py-2 border-b border-slate-700 flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Call Feed</span>
        {feed.length > 0 && (
          <span className="ml-auto text-xs text-slate-500">{feed.length} calls</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto scroll-thin p-2">
        {feed.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 text-sm gap-2">
            <span className="text-3xl">📞</span>
            <span>Waiting for calls…</span>
            <span className="text-xs text-slate-700">Start a scenario or submit a manual call</span>
          </div>
        ) : (
          feed.map((item) => (
            <IncidentCard key={item.call_id} item={item} />
          ))
        )}
      </div>
    </div>
  )
}
