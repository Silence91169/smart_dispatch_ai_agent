import { useEffect, useRef } from 'react'
import { LiveSocket } from '../api/websocket'
import { api } from '../api/client'
import { useSystemStore } from '../store/useSystemStore'
import { handleWsEvent } from '../store/eventHandlers'

export function useLiveConnection() {
  const socketRef = useRef(null)
  const setGraph = useSystemStore((s) => s.setGraph)
  const buildNodeIndex = useSystemStore((s) => s.buildNodeIndex)
  const setResources = useSystemStore((s) => s.setResources)
  const setIncidents = useSystemStore((s) => s.setIncidents)
  const setStats = useSystemStore((s) => s.setStats)
  const setSimulation = useSystemStore((s) => s.setSimulation)
  const setConnectionStatus = useSystemStore((s) => s.setConnectionStatus)

  useEffect(() => {
    let cancelled = false

    // 1. Hydrate initial state from REST before opening the socket.
    ;(async () => {
      try {
        const [graph, resources, incidents, stats, simStatus] = await Promise.all([
          api.getGraph(),
          api.getResources(),
          api.getIncidents({ limit: 200 }),
          api.getStats().catch(() => null),
          api.getSimulationStatus().catch(() => null),
        ])
        if (cancelled) return
        setGraph(graph)
        buildNodeIndex()
        setResources(resources)
        setIncidents(incidents)
        if (stats) setStats(stats)
        if (simStatus) setSimulation(simStatus)
      } catch (err) {
        console.error('Initial hydration failed:', err)
      }
    })()

    // 2. Open the WebSocket (history replay fills in recent events).
    const sock = new LiveSocket({
      onEvent: handleWsEvent,
      onStatusChange: setConnectionStatus,
    })
    sock.connect()
    socketRef.current = sock

    // 3. Periodic REST refresh so REST state stays in sync (5 s cadence).
    const refreshInterval = setInterval(async () => {
      try {
        const [resources, stats, simStatus] = await Promise.all([
          api.getResources(),
          api.getStats(),
          api.getSimulationStatus(),
        ])
        setResources(resources)
        setStats(stats)
        setSimulation(simStatus)
      } catch {
        // ignore transient failures
      }
    }, 5000)

    return () => {
      cancelled = true
      clearInterval(refreshInterval)
      sock.disconnect()
    }
  }, [])
}
