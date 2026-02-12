from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path("artifacts/reports")
OUTPUT_FILE = OUTPUT_DIR / "geo_pipeline_report.json"
INTERMEDIATE_DIR = Path("artifacts/intermediate")
INCLUDED_OUTPUT_FILE = INTERMEDIATE_DIR / "included_edges.json"
DEFAULT_INPUT_FILE = Path("services/geo-pipeline/data/sample_osm_edges.json")

INCLUDED_HIGHWAYS = {
    "footway",
    "pedestrian",
    "path",
    "residential",
    "living_street",
    "service",
    "tertiary",
    "tertiary_link",
    "secondary",
    "secondary_link",
    "primary",
    "primary_link",
    "unclassified",
}

EXCLUDED_HIGHWAYS = {"motorway", "motorway_link", "trunk", "trunk_link"}


def should_include(edge: dict[str, Any], *, allow_steps: bool) -> tuple[bool, str]:
    highway = edge.get("highway")
    access = edge.get("access")
    foot = edge.get("foot")

    if not highway:
        return False, "missing_highway"
    if highway in EXCLUDED_HIGHWAYS:
        return False, "highway_excluded"
    if access == "private" or foot == "private":
        return False, "private_access"
    if foot == "no":
        return False, "foot_forbidden"
    if highway == "steps" and not allow_steps:
        return False, "steps_disabled_mvp"
    if highway == "steps" and allow_steps:
        return True, "included_steps"
    if highway in INCLUDED_HIGHWAYS:
        return True, "included_highway"
    return False, "unknown_highway"


def load_edges(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        raise ValueError("Invalid input format: 'edges' must be a list")
    return edges


def main() -> None:
    parser = argparse.ArgumentParser(description="Run geo pipeline filtering")
    parser.add_argument("--allow-steps", action="store_true", help="Include highway=steps")
    parser.add_argument(
        "--input-file",
        default=str(DEFAULT_INPUT_FILE),
        help="Local edges JSON file with {'edges': [...]} format",
    )
    args = parser.parse_args()

    input_file = Path(args.input_file)
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}. Use local extract JSON or fetch with fetch_overpass.py"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    edges = load_edges(input_file)
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    exclusion_reasons: Counter[str] = Counter()

    for edge in edges:
        keep, reason = should_include(edge, allow_steps=args.allow_steps)
        if keep:
            included.append(edge)
        else:
            exclusion_reasons[reason] += 1
            excluded.append(edge)

    INCLUDED_OUTPUT_FILE.write_text(json.dumps({"edges": included}, indent=2), encoding="utf-8")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "config": {
            "allow_steps": args.allow_steps,
            "input_file": str(input_file),
        },
        "counts": {
            "total_edges": len(edges),
            "included_edges": len(included),
            "excluded_edges": len(excluded),
        },
        "exclusion_reasons": dict(exclusion_reasons),
        "outputs": {
            "included_edges_file": str(INCLUDED_OUTPUT_FILE),
        },
        "next_action": "Build global route from included edges and segment into GPX",
    }

    OUTPUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report generated: {OUTPUT_FILE}")
    print(f"Included edges written: {INCLUDED_OUTPUT_FILE}")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
