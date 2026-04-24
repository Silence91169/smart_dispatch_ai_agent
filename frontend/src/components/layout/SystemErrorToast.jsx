import { useEffect } from 'react'
import { useSystemStore } from '../../store/useSystemStore'

export default function SystemErrorToast() {
  const systemError = useSystemStore((s) => s.systemError)
  const clearSystemError = useSystemStore((s) => s.clearSystemError)

  useEffect(() => {
    if (!systemError) return
    const timer = setTimeout(clearSystemError, 5000)
    return () => clearTimeout(timer)
  }, [systemError?.id])

  if (!systemError) return null

  return (
    <div className="fixed top-12 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex items-center gap-3 bg-red-900 border border-red-600 text-red-100 text-xs font-medium px-4 py-2.5 rounded-lg shadow-xl">
        <span className="text-base">⚠️</span>
        <span>{systemError.message}</span>
        <button
          onClick={clearSystemError}
          className="ml-2 text-red-300 hover:text-red-100 text-sm leading-none"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
