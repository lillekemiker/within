# CLI entry point


import argparse
from typing import cast

from within.address import Address
from within.routing import POSSIBLE_TRANSPORTATION_MODES, Route, Routing, TransportModeT

try:
    import plotly.express as px
except ImportError:
    px = None

ZOOM_LEVEL = 13


class ArgNamespaceT(argparse.Namespace):
    start: Address
    destination: Address
    transport_mode: TransportModeT
    num_suggestions: int
    show_map: bool


def get_args() -> ArgNamespaceT:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, type=Address, help="Start address")
    parser.add_argument(
        "--destination", required=True, type=Address, help="Where you want to go"
    )
    parser.add_argument(
        "--transport-mode",
        choices=POSSIBLE_TRANSPORTATION_MODES,
        default="drive",
        help="Mode of transpotation",
    )
    parser.add_argument("--num-suggestions", type=int, default=1)
    parser.add_argument(
        "--show-map", action="store_true", help="Visualize route on map"
    )
    return cast(ArgNamespaceT, parser.parse_args())


def show_map(route: Route, zoom: int) -> None:
    fig = px.line_map(
        route.path_coordinates, lat="lat", lon="lon", map_style="streets", zoom=zoom
    )
    fig.show()


def main() -> None:
    args = get_args()
    if args.show_map and px is None:
        print("For map visualization support run `pip install within[map]`")
        raise SystemExit(-1)
    print(
        f"{args.start.location_description}: {args.start.latitude}, {args.start.longitude}"
    )
    print(
        f"{args.destination.location_description}: {args.destination.latitude}, {args.destination.longitude}"
    )
    print()
    routing = Routing(args.start, args.destination, args.transport_mode)
    routes = routing.shortest_routes(args.num_suggestions)
    for route in routes:
        print("\n".join(route.description))
        print(f"Total route length: {route.total_length_m / 1000:.1f} km\n\n")
        if args.show_map:
            show_map(route, ZOOM_LEVEL)
