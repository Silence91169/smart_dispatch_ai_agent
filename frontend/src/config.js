export const API_BASE = import.meta.env.VITE_API_BASE || '/api'
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live'
export const WS_RECONNECT_DELAY_MS = 2000
export const WS_MAX_RECONNECT_ATTEMPTS = 10

export const EVENT_TYPES = {
  CALL_RECEIVED: 'call_received',
  TRIAGE_STARTED: 'triage_started',
  TRIAGE_COMPLETED: 'triage_completed',
  TRIAGE_FAILED: 'triage_failed',
  DUPLICATE_DETECTED: 'duplicate_detected',
  INCIDENT_CREATED: 'incident_created',
  INCIDENT_UPDATED: 'incident_updated',
  DISPATCH_DECIDED: 'dispatch_decided',
  RESOURCE_DISPATCHED: 'resource_dispatched',
  RESOURCE_STATUS_CHANGED: 'resource_status_changed',
  RESOURCE_REASSIGNED: 'resource_reassigned',
  UNFULFILLED_INCIDENT: 'unfulfilled_incident',
  SIMULATION_STARTED: 'simulation_started',
  SIMULATION_STOPPED: 'simulation_stopped',
  SIMULATION_PROGRESS: 'simulation_progress',
  SYSTEM_ERROR: 'system_error',
}

export const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
}

export const RESOURCE_STATUS_COLORS = {
  available: '#22c55e',
  dispatched: '#f59e0b',
  en_route: '#f59e0b',
  on_scene: '#3b82f6',
  returning: '#6b7280',
  out_of_service: '#7f1d1d',
}

export const SCENARIO_OPTIONS = [
  { value: 'earthquake_chaos', label: '🌋 Earthquake Chaos (30 calls)' },
  { value: 'quiet_night',      label: '🌙 Quiet Night (10 calls)' },
  { value: 'overload_test',    label: '⚡ Overload Test (50 calls)' },
  { value: 'crime_wave',       label: '🔫 Crime Wave (20 calls)' },
  { value: 'highway_incident', label: '🚗 Highway Incident (15 calls)' },
]
