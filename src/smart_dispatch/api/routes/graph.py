"""GET /graph — city road network + resource positions."""

from fastapi import APIRouter, Depends

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import GraphStateResponse
from smart_dispatch.data.city_graph import get_city_graph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_model=GraphStateResponse)
async def get_graph_state(
    state: AppState = Depends(get_state),
) -> GraphStateResponse:
    city = get_city_graph()
    G = city.graph  # underlying networkx.Graph

    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({"id": node_id, **{k: v for k, v in data.items()}})

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({"from": u, "to": v, **{k: v for k, v in data.items()}})

    resources = await state.db.list_resources()
    resource_list = [
        {
            "id": r.id,
            "call_sign": r.call_sign,
            "resource_type": r.resource_type,
            "status": r.status,
            "current_node_id": r.current_node_id,
            "current_incident_id": r.current_incident_id,
        }
        for r in resources
    ]

    return GraphStateResponse(nodes=nodes, edges=edges, resources=resource_list)
