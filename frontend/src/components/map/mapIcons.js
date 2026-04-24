import L from 'leaflet'
import { SEVERITY_COLORS, RESOURCE_STATUS_COLORS } from '../../config'

export function buildIncidentIcon(severity) {
  const color = SEVERITY_COLORS[severity] || '#6b7280'
  const pulse = severity === 'CRITICAL' || severity === 'HIGH'
  const html = `
    <div style="position:relative;display:flex;align-items:center;justify-content:center;width:24px;height:24px;">
      ${pulse ? `<span class="marker-ping" style="position:absolute;width:24px;height:24px;border-radius:50%;background:${color};opacity:0.55;"></span>` : ''}
      <span style="position:relative;width:14px;height:14px;border-radius:50%;border:2px solid white;background:${color};box-shadow:0 0 8px ${color};display:inline-block;"></span>
    </div>`
  return L.divIcon({ html, className: 'incident-marker', iconSize: [24, 24], iconAnchor: [12, 12] })
}

export const TYPE_EMOJI = {
  ambulance:   '🚑',
  fire_truck:  '🚒',
  police_car:  '🚓',
  hazmat_unit: '⚠️',
}

export function buildVehicleIcon(type, status) {
  const color = RESOURCE_STATUS_COLORS[status] || '#64748b'
  const emoji = TYPE_EMOJI[type] || '🚐'
  const html = `<div style="font-size:20px;line-height:1;filter:drop-shadow(0 0 4px ${color});text-align:center;">${emoji}</div>`
  return L.divIcon({ html, className: 'vehicle-marker', iconSize: [28, 28], iconAnchor: [14, 14] })
}
