import { Polyline } from 'react-leaflet'
import { useSystemStore } from '../../store/useSystemStore'

export default function RouteLine({ resourceId }) {
  const route = useSystemStore((s) => s.activeRoutes[resourceId])
  const nodeById = useSystemStore((s) => s.nodeById)

  if (!route || !route.path || route.path.length < 2) return null

  const points = route.path
    .map((nid) => nodeById[nid])
    .filter(Boolean)
    .map((n) => [n.lat, n.lng])

  if (points.length < 2) return null

  return (
    <Polyline
      positions={points}
      pathOptions={{ color: '#f59e0b', weight: 4, opacity: 0.75, dashArray: '6 8' }}
    />
  )
}
