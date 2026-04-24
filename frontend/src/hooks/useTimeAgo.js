import { useState, useEffect } from 'react'

function format(ts) {
  const diff = (Date.now() - new Date(ts).getTime()) / 1000
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

export function useTimeAgo(timestamp) {
  const [label, setLabel] = useState(() => (timestamp ? format(timestamp) : ''))

  useEffect(() => {
    if (!timestamp) return
    const id = setInterval(() => setLabel(format(timestamp)), 5000)
    return () => clearInterval(id)
  }, [timestamp])

  return label
}
