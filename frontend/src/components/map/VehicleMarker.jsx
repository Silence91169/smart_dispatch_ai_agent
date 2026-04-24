import { useEffect, useRef, useState } from 'react'
import { Marker, Tooltip } from 'react-leaflet'
import { useSystemStore } from '../../store/useSystemStore'
import { buildVehicleIcon } from './mapIcons'

/** Interpolate along a multi-segment path at fraction t ∈ [0,1]. */
function interpolate(nodes, t) {
  if (!nodes.length) return null
  if (nodes.length === 1 || t <= 0) return [nodes[0].lat, nodes[0].lng]
  if (t >= 1) return [nodes[nodes.length - 1].lat, nodes[nodes.length - 1].lng]

  const segs = []
  let total = 0
  for (let i = 0; i < nodes.length - 1; i++) {
    const d = Math.hypot(nodes[i + 1].lat - nodes[i].lat, nodes[i + 1].lng - nodes[i].lng)
    segs.push(d)
    total += d
  }
  const target = t * total
  let accum = 0
  for (let i = 0; i < segs.length; i++) {
    if (accum + segs[i] >= target) {
      const local = (target - accum) / (segs[i] || 1)
      return [
        nodes[i].lat + (nodes[i + 1].lat - nodes[i].lat) * local,
        nodes[i].lng + (nodes[i + 1].lng - nodes[i].lng) * local,
      ]
    }
    accum += segs[i]
  }
  return [nodes[nodes.length - 1].lat, nodes[nodes.length - 1].lng]
}

export default function VehicleMarker({ resource }) {
  const nodeById = useSystemStore((s) => s.nodeById)
  const route = useSystemStore((s) => s.activeRoutes[resource.id])
  const dispatchCount = useSystemStore((s) => s.resourceDispatchCounts[resource.id] || 0)
  const [tick, setTick] = useState(0)
  const timerRef = useRef(null)

  // Tick at ~10 fps while this vehicle is moving
  useEffect(() => {
    if (!route || !route.path || route.path.length < 2) {
      if (timerRef.current) clearTimeout(timerRef.current)
      return
    }
    let alive = true
    const loop = () => {
      if (!alive) return
      setTick((n) => n + 1)
      timerRef.current = setTimeout(loop, 100)
    }
    loop()
    return () => {
      alive = false
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [route])

  // Resolve current map position
  let position = null
  if (route && route.path?.length >= 2) {
    const pts = route.path.map((nid) => nodeById[nid]).filter(Boolean)
    if (pts.length >= 2) {
      const elapsed = (Date.now() - route.startedAt) / 1000
      const t = Math.min(1, elapsed / Math.max(route.etaSec, 1))
      position = interpolate(pts, t)
    }
  }
  if (!position) {
    const home = nodeById[resource.current_node_id]
    position = home ? [home.lat, home.lng] : null
  }
  if (!position) return null

  const icon = buildVehicleIcon(resource.resource_type, resource.status)
  const etaMin = route ? (route.etaSec / 60).toFixed(1) : null

  return (
    <Marker position={position} icon={icon} zIndexOffset={route ? 500 : 0}>
      <Tooltip direction="top" offset={[0, -12]} opacity={0.95}>
        <div style={{ background: '#0f172a', color: '#e2e8f0', borderRadius: 4, padding: '4px 8px', fontSize: 12 }}>
          <div style={{ fontWeight: 700 }}>{resource.call_sign}</div>
          <div style={{ opacity: 0.75 }}>{resource.status}</div>
          {etaMin && <div style={{ color: '#f59e0b' }}>ETA {etaMin} min</div>}
          {route?.was_reassigned_from && (
            <div style={{ color: '#fb923c', fontWeight: 700 }}>↺ Re-routed</div>
          )}
          {dispatchCount > 0 && (
            <div style={{ opacity: 0.5, fontSize: 10 }}>{dispatchCount} dispatch{dispatchCount !== 1 ? 'es' : ''}</div>
          )}
        </div>
      </Tooltip>
    </Marker>
  )
}
