import { useState } from 'react'
import { Send } from 'lucide-react'
import { api } from '../../api/client'

const EXAMPLES = [
  'bhai fire at CP, 3 log phase hai andar',
  'aunty ji collapse ho gayi near AIIMS, not breathing',
  'accident at Nehru Place, 2 cars, someone bleeding badly',
]

export default function ManualCallInput() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)  // null | 'ok' | 'err'
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim()) return
    setLoading(true)
    setStatus(null)
    try {
      const result = await api.ingestCall(text.trim())
      if (result.skipped && result.skip_reason?.includes('rate_limit')) {
        setStatus('err')
        setMessage('Rate limit — try again shortly')
      } else if (result.skipped) {
        setStatus('err')
        setMessage(result.skip_reason || 'Call skipped')
      } else {
        setStatus('ok')
        setMessage(`✓ ${result.triage?.incident_type || 'Incident'} created`)
        setText('')
      }
    } catch (e) {
      setStatus('err')
      setMessage(e.message.slice(0, 80))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-3 flex flex-col gap-2">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Manual Call</span>

      <div className="flex flex-wrap gap-1">
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => setText(ex)}
            className="text-[9px] text-slate-500 hover:text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded px-1.5 py-0.5 transition-colors truncate max-w-[140px]"
            title={ex}
          >
            {ex.slice(0, 28)}…
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a 112 call transcript…"
          rows={2}
          disabled={loading}
          className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-xs text-slate-200 placeholder-slate-600 resize-none disabled:opacity-40 focus:outline-none focus:border-slate-400"
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-semibold px-3 rounded transition-colors"
        >
          <Send size={11} />
          {loading ? '…' : 'Send'}
        </button>
      </form>

      {status && (
        <p className={`text-[10px] ${status === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
          {message}
        </p>
      )}
    </div>
  )
}
