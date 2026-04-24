import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function ReasoningBubble({ reasoning, alternatives = [] }) {
  const [expanded, setExpanded] = useState(false)

  if (!reasoning) return null

  return (
    <div className="mt-2">
      <blockquote className="border-l-2 border-slate-500 pl-3 text-xs text-slate-300 leading-relaxed italic">
        "{reasoning}"
      </blockquote>

      {alternatives.length > 0 && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center gap-1 transition-colors"
          >
            {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            {alternatives.length} alternative{alternatives.length !== 1 ? 's' : ''} considered
          </button>
          {expanded && (
            <ul className="mt-1.5 space-y-1">
              {alternatives.map((a, i) => (
                <li key={i} className="text-[10px] flex items-center gap-2 text-slate-400">
                  <span className={`w-1.5 h-1.5 rounded-full ${a.chosen ? 'bg-green-500' : 'bg-slate-600'}`} />
                  <span className="font-medium text-slate-300">{a.call_sign}</span>
                  <span>ETA {(a.eta_sec / 60).toFixed(1)}min</span>
                  <span className="opacity-60">{a.status}</span>
                  {a.chosen && <span className="text-green-400 font-semibold">✓</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
