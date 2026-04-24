import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from 'react-leaflet'
import { useSystemStore } from '../../store/useSystemStore'
import IncidentMarker from './IncidentMarker'
import VehicleMarker from './VehicleMarker'
import RouteLine from './RouteLine'

const DELHI_CENTER = [28.6139, 77.209]

export default function CityMap() {
  const graph = useSystemStore((s) => s.graph)
  const incidents = useSystemStore((s) => s.incidents)
  const resources = useSystemStore((s) => s.resources)
  const activeRoutes = useSystemStore((s) => s.activeRoutes)
  const nodeById = useSystemStore((s) => s.nodeById)

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={DELHI_CENTER}
        zoom={11}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Road edges — backend returns { from: "N01", to: "N02", ... } */}
        {graph.edges.map((e, i) => {
          const a = nodeById[e.from]
          const b = nodeById[e.to]
          if (!a || !b) return null
          return (
            <Polyline
              key={`edge-${i}`}
              positions={[[a.lat, a.lng], [b.lat, b.lng]]}
              pathOptions={{ color: '#334155', weight: 2, opacity: 0.5 }}
            />
          )
        })}

        {/* Landmark nodes — backend returns { id: "N01", name: "...", lat, lng } */}
        {graph.nodes.map((n) => (
          <CircleMarker
            key={n.id}
            center={[n.lat, n.lng]}
            radius={5}
            pathOptions={{ color: '#475569', fillColor: '#94a3b8', fillOpacity: 0.85, weight: 1 }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.92}>
              <span style={{ fontSize: 11 }}>{n.name}</span>
            </Tooltip>
          </CircleMarker>
        ))}

        {/* Active route lines (dispatched vehicles) */}
        {Object.keys(activeRoutes).map((resId) => (
          <RouteLine key={`route-${resId}`} resourceId={resId} />
        ))}

        {/* Incident pins */}
        {Object.values(incidents).map((inc) => {
          const node = nodeById[inc.location_node_id]
          if (!node) return null
          return (
            <IncidentMarker
              key={inc.id || inc.incident_id}
              incident={inc}
              position={[node.lat, node.lng]}
            />
          )
        })}

        {/* Vehicle markers */}
        {Object.values(resources).map((r) => (
          <VehicleMarker key={r.id} resource={r} />
        ))}
      </MapContainer>
    </div>
  )
}
