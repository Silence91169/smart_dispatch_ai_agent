import { EVENT_TYPES } from '../config'
import { useSystemStore } from './useSystemStore'

export function handleWsEvent(event) {
  const store = useSystemStore.getState()

  switch (event.type) {
    case EVENT_TYPES.CALL_RECEIVED:
      store.pushFeedItem({
        call_id: event.call_id,
        transcript: event.payload?.transcript || '',
        timestamp: event.timestamp,
        triage: null,
        dispatch: null,
        stage: 'triage_pending',
        incident_id: null,
        error: null,
      })
      store.bumpCounter('totalCalls')
      break

    case EVENT_TYPES.TRIAGE_COMPLETED:
      store.updateFeedItem(event.call_id, {
        triage: event.payload,
        stage: event.payload?.is_duplicate ? 'duplicate' : 'dispatch_pending',
        incident_id: event.incident_id,
      })
      if (event.payload?.is_duplicate) store.bumpCounter('totalDuplicates')
      break

    case EVENT_TYPES.TRIAGE_FAILED:
      store.updateFeedItem(event.call_id, {
        stage: 'error',
        error: event.payload?.error || 'Triage failed',
      })
      break

    case EVENT_TYPES.DUPLICATE_DETECTED:
      store.updateFeedItem(event.call_id, {
        stage: 'duplicate',
        duplicateOf: event.payload?.duplicate_of_call_id,
        similarity: event.payload?.similarity,
      })
      break

    case EVENT_TYPES.INCIDENT_CREATED:
      store.upsertIncident({
        id: event.incident_id,
        ...event.payload,
        status: 'pending',
      })
      store.bumpCounter('totalIncidents')
      break

    case EVENT_TYPES.DISPATCH_DECIDED:
      store.pushDecision({ ...event.payload, incident_id: event.incident_id })
      store.upsertIncident({ id: event.incident_id, status: event.payload?.status || 'dispatched' })
      store.updateFeedItem(event.payload?.call_id || '', { dispatch: event.payload })
      break

    case EVENT_TYPES.RESOURCE_DISPATCHED: {
      const { resource_id, payload, incident_id } = event
      store.upsertResource({
        id: resource_id,
        call_sign: payload?.call_sign,
        status: 'en_route',
        current_incident_id: incident_id,
        current_node_id: payload?.from_node_id,
      })
      store.setActiveRoute(resource_id, {
        from_node_id: payload?.from_node_id,
        to_node_id: payload?.to_node_id,
        path: payload?.path || [],
        startedAt: Date.now(),
        etaSec: payload?.travel_time_sec || 0,
        incident_id,
        was_reassigned_from: payload?.was_reassigned_from || null,
      })
      store.bumpCounter('totalDispatches')
      store.bumpResourceDispatch(resource_id)
      break
    }

    case EVENT_TYPES.RESOURCE_STATUS_CHANGED:
      store.upsertResource({
        id: event.resource_id,
        status: event.payload?.status,
        current_node_id: event.payload?.current_node_id,
      })
      // If vehicle is now back to available, clear its route
      if (event.payload?.status === 'available') {
        store.clearActiveRoute(event.resource_id)
      }
      break

    case EVENT_TYPES.RESOURCE_REASSIGNED:
      store.bumpCounter('totalReassignments')
      break

    case EVENT_TYPES.UNFULFILLED_INCIDENT:
      store.bumpCounter('unfulfilledCount')
      store.upsertIncident({ id: event.incident_id, status: 'unfulfillable' })
      break

    case EVENT_TYPES.SIMULATION_STARTED:
      store.setSimulation({ is_running: true, stats: event.payload })
      break

    case EVENT_TYPES.SIMULATION_STOPPED:
      store.setSimulation({ is_running: false, stats: event.payload })
      break

    case EVENT_TYPES.SIMULATION_PROGRESS:
      store.setSimulation({ is_running: true, stats: event.payload })
      break

    case EVENT_TYPES.SYSTEM_ERROR:
      store.showSystemError(event.payload?.message || 'System error')
      break

    default:
      break
  }
}
