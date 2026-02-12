from __future__ import annotations

import argparse
import json
from pathlib import Path

INPUT_FILE = Path("artifacts/intermediate/included_edges.json")
OUTPUT_DIR = Path("artifacts/routes")
OUTPUT_FILE = OUTPUT_DIR / "global_route.geojson"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a demo global route from included edges")
    parser.add_argument("--input-file", default=str(INPUT_FILE), help="Filtered edges JSON")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}. Run run_pipeline.py first.")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    edges = data.get("edges", [])

    features = []
    route_coords: list[list[float]] = []

    for edge in edges:
        geometry = edge.get("geometry") or []
        if len(geometry) < 2:
            continue

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": edge.get("id"),
                    "highway": edge.get("highway"),
                    "length_m": edge.get("length_m"),
                },
                "geometry": {"type": "LineString", "coordinates": geometry},
            }
        )

        if not route_coords:
            route_coords.extend(geometry)
        else:
            if route_coords[-1] == geometry[0]:
                route_coords.extend(geometry[1:])
            else:
                route_coords.extend(geometry)

    if len(route_coords) < 2:
        raise ValueError("No usable geometries found in included edges")

    global_feature = {
        "type": "Feature",
        "properties": {"name": "global_route_demo", "source": str(input_path)},
        "geometry": {"type": "LineString", "coordinates": route_coords},
    }

    collection = {
        "type": "FeatureCollection",
        "features": [global_feature, *features],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Global route generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
