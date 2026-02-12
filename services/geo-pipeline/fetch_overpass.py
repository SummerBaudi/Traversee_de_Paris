from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_query(bbox: str) -> str:
    return f"""
[out:json][timeout:60];
(
  way["highway"]({bbox});
);
out tags geom;
""".strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OSM ways from Overpass and save as local JSON")
    parser.add_argument("--bbox", required=True, help="south,west,north,east")
    parser.add_argument(
        "--output",
        default="services/geo-pipeline/data/overpass_edges.json",
        help="Output JSON file path",
    )
    args = parser.parse_args()

    query = build_query(args.bbox)
    response = requests.post(OVERPASS_URL, data={"data": query}, timeout=120)
    response.raise_for_status()
    payload = response.json()

    edges = []
    for element in payload.get("elements", []):
        if element.get("type") != "way":
            continue
        tags = element.get("tags", {})
        edge = {
            "id": element.get("id"),
            "highway": tags.get("highway"),
            "access": tags.get("access"),
            "foot": tags.get("foot"),
        }
        edges.append(edge)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"edges": edges}, indent=2), encoding="utf-8")
    print(f"Saved {len(edges)} edges to {out}")


if __name__ == "__main__":
    main()
