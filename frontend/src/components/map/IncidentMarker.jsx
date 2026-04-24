import { Marker, Popup } from 'react-leaflet'
import { useSystemStore } from '../../store/useSystemStore'
import { buildIncidentIcon } from './mapIcons'
import { SEVERITY_COLORS } from '../../config'

export default function IncidentMarker({ incident, position }) {
  const selectIncident = useSystemStore((s) => s.selectIncident)
  const icon = buildIncidentIcon(incident.severity)
  const color = SEVERITY_COLORS[incident.severity] || '#6b7280'

  return (
    <Marker
      position={position}
      icon={icon}
      eventHandlers={{ click: () => selectIncident(incident.id || incident.incident_id) }}
    >
      <Popup className="dark-popup">
        <div style={{ background: '#1e293b', color: '#e2e8f0', borderRadius: 6, padding: '8px 10px', minWidth: 180 }}>
          <div style={{ fontWeight: 700, marginBottom: 2, color }}>
            {incident.incident_type} · {incident.severity}
          </div>
          <div style={{ fontSize: 12, opacity: 0.8 }}>
            {incident.summary || incident.location_raw || ''}
          </div>
          <div style={{ fontSize: 11, marginTop: 4, opacity: 0.6 }}>
            Status: <span style={{ color: '#94a3b8' }}>{incident.status || 'pending'}</span>
          </div>
          {incident.duplicate_call_count > 1 && (
            <div style={{ fontSize: 11, color: '#f59e0b', marginTop: 2 }}>
              +{incident.duplicate_call_count - 1} duplicate call(s)
            </div>
          )}
        </div>
      </Popup>
    </Marker>
  )
}
