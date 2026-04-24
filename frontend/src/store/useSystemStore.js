import { create } from 'zustand'

const MAX_FEED = 60
const MAX_DECISIONS = 40

export const useSystemStore = create((set, get) => ({
  // ── Connection ─────────────────────────────────────────────────────────────
  connectionStatus: 'disconnected',
  setConnectionStatus: (s) => set({ connectionStatus: s }),

  // ── Graph ──────────────────────────────────────────────────────────────────
  graph: { nodes: [], edges: [] },
  setGraph: (g) => set({ graph: g }),
  nodeById: {},  // populated by buildNodeIndex()

  // ── Incidents (keyed by incident_id) ──────────────────────────────────────
  incidents: {},
  upsertIncident: (inc) =>
    set((state) => {
      const key = inc.id || inc.incident_id
      if (!key) return {}
      return {
        incidents: {
          ...state.incidents,
          [key]: { ...(state.incidents[key] || {}), ...inc },
        },
      }
    }),
  setIncidents: (list) =>
    set(() => {
      const map = {}
      for (const i of list) {
        const key = i.incident_id || i.id
        if (key) map[key] = { id: key, ...i }
      }
      return { incidents: map }
    }),

  // ── Resources (keyed by id) ────────────────────────────────────────────────
  resources: {},
  setResources: (list) =>
    set(() => {
      const map = {}
      for (const r of list) map[r.id] = r
      return { resources: map }
    }),
  upsertResource: (r) =>
    set((state) => ({
      resources: {
        ...state.resources,
        [r.id]: { ...(state.resources[r.id] || {}), ...r },
      },
    })),

  // ── Live feed (most recent first, bounded at MAX_FEED) ────────────────────
  feed: [],
  pushFeedItem: (item) =>
    set((state) => ({ feed: [item, ...state.feed].slice(0, MAX_FEED) })),
  updateFeedItem: (call_id, patch) =>
    set((state) => ({
      feed: state.feed.map((f) => (f.call_id === call_id ? { ...f, ...patch } : f)),
    })),

  // ── Decisions (most recent first) ─────────────────────────────────────────
  decisions: [],
  pushDecision: (d) =>
    set((state) => ({ decisions: [d, ...state.decisions].slice(0, MAX_DECISIONS) })),

  // ── Active vehicle routes ─────────────────────────────────────────────────
  // resource_id → { from_node_id, to_node_id, path[], startedAt, etaSec, incident_id, was_reassigned_from }
  activeRoutes: {},
  setActiveRoute: (resource_id, route) =>
    set((state) => ({ activeRoutes: { ...state.activeRoutes, [resource_id]: route } })),
  clearActiveRoute: (resource_id) =>
    set((state) => {
      const { [resource_id]: _, ...rest } = state.activeRoutes
      return { activeRoutes: rest }
    }),

  // ── Stats ──────────────────────────────────────────────────────────────────
  stats: null,
  setStats: (s) => set({ stats: s }),

  // ── Simulation ─────────────────────────────────────────────────────────────
  simulation: { is_running: false, stats: {} },
  setSimulation: (s) => set({ simulation: s }),

  // ── UI selection ───────────────────────────────────────────────────────────
  selectedIncidentId: null,
  selectIncident: (id) => set({ selectedIncidentId: id }),

  // ── Live counters ──────────────────────────────────────────────────────────
  counters: {
    totalCalls: 0,
    totalDuplicates: 0,
    totalIncidents: 0,
    totalDispatches: 0,
    totalReassignments: 0,
    unfulfilledCount: 0,
  },
  bumpCounter: (key, n = 1) =>
    set((state) => ({
      counters: { ...state.counters, [key]: (state.counters[key] || 0) + n },
    })),

  // Per-resource dispatch count (tracked via events since REST doesn't expose it)
  resourceDispatchCounts: {},
  bumpResourceDispatch: (resource_id) =>
    set((state) => ({
      resourceDispatchCounts: {
        ...state.resourceDispatchCounts,
        [resource_id]: (state.resourceDispatchCounts[resource_id] || 0) + 1,
      },
    })),

  // ── Build node index from graph ────────────────────────────────────────────
  // Backend returns nodes with `id` field (e.g. "N01"), not `node_id`.
  buildNodeIndex: () => {
    const { graph } = get()
    const idx = {}
    for (const n of graph.nodes) idx[n.id] = n
    set({ nodeById: idx })
  },
}))
