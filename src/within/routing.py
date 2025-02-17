# Main interface class

from typing import Dict, List, Literal, Optional, Tuple

import osmnx
from networkx import MultiDiGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from within.address import Address
from within.spherical_geometry import (
    get_bearing,
    get_cardinal_direction,
    get_turning_instruction,
    great_circle_distance,
    great_circle_halfway_point,
)

TransportModeT = Literal["all", "all_public", "bike", "drive", "drive_service", "walk"]
POSSIBLE_TRANSPORTATION_MODES: List[TransportModeT] = [
    # "all",
    "all_public",
    "bike",
    "drive",
    "drive_service",
    "walk",
]


def _format_distance(dist_m: float) -> str:
    if dist_m > 9999:
        return f"{dist_m / 1000:.0f} km"
    elif dist_m > 999:
        return f"{dist_m / 1000:.1f} km"
    return f"{dist_m:.0f} m"


class EdgeDataT(TypedDict, total=False):
    length: float
    name: str | List[str]


class NodeT(TypedDict):
    x: float
    y: float


class Route(BaseModel):
    node_idx: List[int]
    edges: Dict[Tuple[int, int], EdgeDataT]
    nodes: Dict[int, NodeT]

    @property
    def path_coordinates(self) -> List[Dict[str, float]]:
        return [
            {"lat": self.nodes[idx]["y"], "lon": self.nodes[idx]["x"]}
            for idx in self.node_idx
        ]

    @property
    def total_length_m(self) -> float:
        return self._get_route_metric("length")

    @property
    def description(self) -> List[str]:
        result: List[str] = []

        current_bearing = new_bearing = self._get_node_to_node_berring(
            self.node_idx[0], self.node_idx[1]
        )
        current_street: str = self._get_street_name(self.node_idx[0], self.node_idx[1])
        acc_street_distance = 0.0
        destination_node_idx = self.node_idx[-1]

        for node_a_idx, node_b_idx in zip(self.node_idx, self.node_idx[1:]):
            street = self._get_street_name(node_a_idx, node_b_idx)
            edge_data = self.edges[(node_a_idx, node_b_idx)]
            edge_length = edge_data.get("length", 0)
            assert isinstance(edge_length, float)
            acc_street_distance += edge_length

            if street == current_street and node_b_idx != destination_node_idx:
                # continuing along the same street - skip instruction
                continue

            # Otherwise turning onto a new street - output the instruction with
            # accumulated travel distance.
            if not result:
                # The first instruction
                init_direction = get_cardinal_direction(current_bearing)
                instruction = f"Head {init_direction} on {current_street} "
                dist_string = _format_distance(acc_street_distance)
                result.append(instruction + f"and continue for {dist_string}")
            else:
                # Turning onto new street
                turn_cardinal_direction = get_cardinal_direction(new_bearing)
                turn_instr = get_turning_instruction(current_bearing, new_bearing)
                instruction = (
                    f"{turn_instr} on {current_street} ({turn_cardinal_direction}) "
                )
                dist_string = _format_distance(acc_street_distance)
                result.append(instruction + f"and continue for {dist_string}")

            current_bearing = new_bearing
            new_bearing = self._get_node_to_node_berring(node_a_idx, node_b_idx)
            current_street = street
            acc_street_distance = 0  # reset on new street
        result.append("Arriving at your destination.")
        return result

    def _get_route_metric(self, metric: Literal["length"]) -> float:
        return sum(
            self.edges[(node_a, node_b)][metric]
            for node_a, node_b in zip(self.node_idx, self.node_idx[1:])
        )

    def _get_node_to_node_berring(self, node_a_idx: int, node_b_idx: int) -> float:
        node_a = self.nodes[node_a_idx]
        node_b = self.nodes[node_b_idx]
        return get_bearing(node_a["y"], node_a["x"], node_b["y"], node_b["x"])

    def _get_street_name(
        self, node_a_idx: int, node_b_idx: int, default: str = "unnamed street"
    ) -> str:
        edge_data = self.edges[(node_a_idx, node_b_idx)]
        street = edge_data.get("name", default)
        if isinstance(street, list):
            # Street as two names
            street = "/".join(street)
        assert isinstance(street, str)
        return street


class Routing:
    _network: Optional[MultiDiGraph] = None
    _origin_node: int
    _dest_node: int
    _origin_node_dist_m: float
    _dest_node_dist_m: float
    _edge_data: Dict[Tuple[int, int], EdgeDataT]

    def __init__(
        self,
        starting_point: Address,
        destination: Address,
        transport_mode: TransportModeT,
    ) -> None:
        self.starting_point = starting_point
        self.destination = destination
        assert (
            transport_mode in POSSIBLE_TRANSPORTATION_MODES
        ), f"invalid transport_mode {transport_mode}"
        self.transport_mode = transport_mode

    @property
    def as_the_crow_flies_distance_km(self) -> float:
        return great_circle_distance(
            self.starting_point.latitude,
            self.starting_point.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )

    @property
    def midway_coordinate(self) -> Tuple[float, float]:
        """
        (latitude, longitude) for halfway point between starting point and destination
        """
        return great_circle_halfway_point(
            self.starting_point.latitude,
            self.starting_point.longitude,
            self.destination.latitude,
            self.destination.longitude,
        )

    @property
    def network(self) -> MultiDiGraph:
        if self._network is None:
            network_radius_m = 1000 * (self.as_the_crow_flies_distance_km / 2 + 1)
            self._network = osmnx.graph.graph_from_point(
                self.midway_coordinate,
                network_radius_m,
                network_type=self.transport_mode,
            )
            origin_node, origin_node_dist_m = osmnx.distance.nearest_nodes(
                self.network,
                self.starting_point.longitude,
                self.starting_point.latitude,
                return_dist=True,
            )
            self._origin_node = int(origin_node)
            self._origin_node_dist_m = float(origin_node_dist_m)
            dest_node, dest_node_dist_m = osmnx.distance.nearest_nodes(
                self.network,
                self.destination.longitude,
                self.destination.latitude,
                return_dist=True,
            )
            self._dest_node = int(dest_node)
            self._dest_node_dist_m = float(dest_node_dist_m)
            self._edge_data = {
                (u, v): edge_data for u, v, edge_data in self.network.edges(data=True)
            }
        return self._network

    def _get_shortest_paths(self, *, k: int = 1, weight_by: str) -> List[Route]:
        idx_paths = osmnx.routing.k_shortest_paths(
            self.network, self._origin_node, self._dest_node, k, weight=weight_by
        )
        return [
            Route(
                node_idx=idx_list,
                edges={
                    (node_a, node_b): self._edge_data[(node_a, node_b)]
                    for node_a, node_b in zip(idx_list, idx_list[1:])
                },
                nodes={idx: self.network.nodes[idx] for idx in idx_list},
            )
            for idx_list in idx_paths
        ]

    def shortest_routes(self, k: int = 1) -> List[Route]:
        return self._get_shortest_paths(k=k, weight_by="length")
