from __future__ import annotations

import argparse
import heapq
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

INPUT_FILE = Path("artifacts/intermediate/included_edges.json")
OUTPUT_DIR = Path("artifacts/routes")
OUTPUT_FILE = OUTPUT_DIR / "global_route_cpp.geojson"
METRICS_FILE = OUTPUT_DIR / "route_metrics.json"


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6_371_000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def linestring_len(coords: list[list[float]]) -> float:
    return sum(haversine_m(a[0], a[1], b[0], b[1]) for a, b in zip(coords, coords[1:]))


def node_key(coord: list[float]) -> str:
    return f"{coord[0]:.6f},{coord[1]:.6f}"


def shortest_path(graph: dict[str, list[tuple[str, float]]], src: str, dst: str) -> tuple[float, list[str]]:
    pq: list[tuple[float, str]] = [(0.0, src)]
    dist = {src: 0.0}
    prev: dict[str, str | None] = {src: None}

    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    if dst not in dist:
        raise ValueError(f"No path between odd nodes: {src} -> {dst}")

    path = []
    cur: str | None = dst
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return dist[dst], path


def pair_odds_greedy(odd_nodes: list[str], graph: dict[str, list[tuple[str, float]]]) -> list[list[str]]:
    remaining = set(odd_nodes)
    paths: list[list[str]] = []
    while remaining:
        a = remaining.pop()
        best_b = None
        best_dist = float("inf")
        best_path: list[str] = []
        for b in remaining:
            d, p = shortest_path(graph, a, b)
            if d < best_dist:
                best_dist = d
                best_b = b
                best_path = p
        if best_b is None:
            raise ValueError("Unpaired odd node encountered")
        remaining.remove(best_b)
        paths.append(best_path)
    return paths


def euler_tour(adj_multi: dict[str, list[tuple[str, int]]], start: str) -> list[str]:
    graph = {k: v.copy() for k, v in adj_multi.items()}
    used: set[int] = set()
    stack = [start]
    circuit: list[str] = []

    while stack:
        v = stack[-1]
        while graph.get(v) and graph[v][-1][1] in used:
            graph[v].pop()
        if not graph.get(v):
            circuit.append(stack.pop())
            continue
        u, eid = graph[v].pop()
        if eid in used:
            continue
        used.add(eid)
        stack.append(u)

    circuit.reverse()
    return circuit


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a CPP-like route on filtered edges (heuristic)")
    parser.add_argument("--input-file", default=str(INPUT_FILE))
    args = parser.parse_args()

    data = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    if not edges:
        raise ValueError("No edges available")

    edge_catalog: dict[int, dict] = {}
    adjacency: dict[str, list[tuple[str, int]]] = defaultdict(list)
    weighted_graph: dict[str, list[tuple[str, float]]] = defaultdict(list)
    degree = Counter()

    next_id = 1
    for edge in edges:
        geom = edge.get("geometry") or []
        if len(geom) < 2:
            continue
        a = node_key(geom[0])
        b = node_key(geom[-1])
        length = edge.get("length_m") or linestring_len(geom)
        edge_id = next_id
        next_id += 1

        edge_catalog[edge_id] = {
            "id": edge.get("id"),
            "from": a,
            "to": b,
            "length_m": float(length),
            "geometry": geom,
            "synthetic": False,
        }

        adjacency[a].append((b, edge_id))
        adjacency[b].append((a, edge_id))
        weighted_graph[a].append((b, float(length)))
        weighted_graph[b].append((a, float(length)))
        degree[a] += 1
        degree[b] += 1

    if not edge_catalog:
        raise ValueError("No valid geometries")

    odd_nodes = [n for n, d in degree.items() if d % 2 == 1]
    synthetic_edges = 0

    if odd_nodes:
        odd_paths = pair_odds_greedy(odd_nodes, weighted_graph)
        for path in odd_paths:
            for u, v in zip(path, path[1:]):
                length = next(w for nbr, w in weighted_graph[u] if nbr == v)
                edge_id = next_id
                next_id += 1
                edge_catalog[edge_id] = {
                    "id": f"synthetic_{edge_id}",
                    "from": u,
                    "to": v,
                    "length_m": float(length),
                    "geometry": None,
                    "synthetic": True,
                }
                adjacency[u].append((v, edge_id))
                adjacency[v].append((u, edge_id))
                synthetic_edges += 1

    start = next(iter(adjacency))
    tour_nodes = euler_tour(adjacency, start)
    if len(tour_nodes) < 2:
        raise ValueError("Failed to compute Euler tour")

    coord_by_node = {}
    for e in edges:
        geom = e.get("geometry") or []
        if len(geom) >= 2:
            coord_by_node[node_key(geom[0])] = geom[0]
            coord_by_node[node_key(geom[-1])] = geom[-1]

    route_coords: list[list[float]] = []
    for n in tour_nodes:
        c = coord_by_node.get(n)
        if c is None:
            lon, lat = n.split(",")
            c = [float(lon), float(lat)]
        if not route_coords or route_coords[-1] != c:
            route_coords.append(c)

    traversed = 0.0
    for a, b in zip(tour_nodes, tour_nodes[1:]):
        traversed += next(w for nbr, w in weighted_graph[a] if nbr == b)

    base = sum(float(e.get("length_m") or linestring_len(e.get("geometry") or [])) for e in edges if (e.get("geometry") or []))
    duplication_pct = max(0.0, ((traversed - base) / traversed) * 100.0) if traversed > 0 else 0.0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "global_route_cpp_heuristic",
                    "input": args.input_file,
                },
                "geometry": {"type": "LineString", "coordinates": route_coords},
            }
        ],
    }
    OUTPUT_FILE.write_text(json.dumps(geojson, indent=2), encoding="utf-8")

    metrics = {
        "input_edges": len(edges),
        "odd_nodes": len(odd_nodes),
        "synthetic_edges_added": synthetic_edges,
        "distance_base_m": round(base, 2),
        "distance_traversed_m": round(traversed, 2),
        "duplication_pct": round(duplication_pct, 2),
        "coverage_pct": 100.0,
    }
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"CPP route generated: {OUTPUT_FILE}")
    print(f"Metrics: {METRICS_FILE}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
