import { API_BASE } from '../config'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

export const api = {
  getGraph: () => request('/graph/'),
  getIncidents: (params = {}) => {
    const q = new URLSearchParams(params).toString()
    return request(`/incidents/${q ? `?${q}` : ''}`)
  },
  getResources: () => request('/resources/'),
  getDecisions: () => request('/decisions/'),
  getStats: () => request('/stats/'),
  getScenarios: () => request('/simulation/scenarios'),
  getSimulationStatus: () => request('/simulation/status'),

  ingestCall: (transcript) =>
    request('/calls/ingest', {
      method: 'POST',
      body: JSON.stringify({ transcript }),
    }),

  startScenario: (scenario_name, speed_multiplier = 10) =>
    request('/simulation/start-scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario_name, speed_multiplier }),
    }),

  stopSimulation: () =>
    request('/simulation/stop', { method: 'POST', body: '{}' }),

  resetSimulation: () =>
    request('/simulation/reset', { method: 'POST', body: '{}' }),

  runEval: (limit = 10) =>
    request(`/eval/golden?limit=${limit}`, { method: 'POST', body: '{}' }),
}
