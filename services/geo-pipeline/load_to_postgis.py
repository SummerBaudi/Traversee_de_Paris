from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

DEFAULT_INPUT = Path("artifacts/intermediate/included_edges.json")


def build_linestring_wkt(coords: list[list[float]]) -> str:
    points = ", ".join([f"{lon} {lat}" for lon, lat in coords])
    return f"LINESTRING({points})"


def load_edges(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    if not isinstance(edges, list):
        raise ValueError("Invalid input format: 'edges' must be a list")
    return edges


def main() -> None:
    parser = argparse.ArgumentParser(description="Load filtered edges into PostGIS")
    parser.add_argument("--input-file", default=str(DEFAULT_INPUT), help="JSON file with {'edges': [...]} format")
    parser.add_argument("--db-url", default="postgresql://trp:trp@localhost:5432/trp", help="PostgreSQL DSN")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print stats without DB writes")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}. Run geo pipeline first.")

    edges = load_edges(input_path)
    valid = [e for e in edges if isinstance(e.get("geometry"), list) and len(e["geometry"]) >= 2]

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_ok",
                    "input_file": str(input_path),
                    "total_edges": len(edges),
                    "valid_geometries": len(valid),
                },
                indent=2,
            )
        )
        return

    if psycopg is None:
        raise RuntimeError("psycopg is required. Install dependencies from services/geo-pipeline/requirements.txt")

    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS geo_edges (
                    id BIGINT PRIMARY KEY,
                    highway TEXT,
                    length_m DOUBLE PRECISION,
                    access TEXT,
                    foot TEXT,
                    geom geometry(LineString, 4326)
                );
                """
            )

            for edge in valid:
                wkt = build_linestring_wkt(edge["geometry"])
                cur.execute(
                    """
                    INSERT INTO geo_edges (id, highway, length_m, access, foot, geom)
                    VALUES (%s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
                    ON CONFLICT (id)
                    DO UPDATE SET
                      highway = EXCLUDED.highway,
                      length_m = EXCLUDED.length_m,
                      access = EXCLUDED.access,
                      foot = EXCLUDED.foot,
                      geom = EXCLUDED.geom;
                    """,
                    (
                        edge.get("id"),
                        edge.get("highway"),
                        edge.get("length_m"),
                        edge.get("access"),
                        edge.get("foot"),
                        wkt,
                    ),
                )

        conn.commit()

    print(
        json.dumps(
            {
                "status": "ok",
                "loaded_edges": len(valid),
                "skipped_edges": len(edges) - len(valid),
                "table": "geo_edges",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
