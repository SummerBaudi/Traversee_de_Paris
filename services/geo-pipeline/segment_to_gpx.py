from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

INPUT_FILE = Path("artifacts/routes/global_route_cpp.geojson")
OUTPUT_DIR = Path("artifacts/gpx")
MANIFEST_FILE = OUTPUT_DIR / "segments_manifest.json"


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6_371_000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def line_distance_m(coords: list[list[float]]) -> float:
    total = 0.0
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]
        total += haversine_m(lon1, lat1, lon2, lat2)
    return total


def write_gpx(path: Path, coords: list[list[float]], name: str) -> None:
    points = "\n".join([f'      <trkpt lat="{lat}" lon="{lon}"></trkpt>' for lon, lat in coords])
    content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<gpx version=\"1.1\" creator=\"Traversee_de_Paris\" xmlns=\"http://www.topografix.com/GPX/1/1\">
  <trk>
    <name>{name}</name>
    <trkseg>
{points}
    </trkseg>
  </trk>
</gpx>
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment global route into GPX files")
    parser.add_argument("--input-file", default=str(INPUT_FILE), help="Global route GeoJSON")
    parser.add_argument("--segment-length-m", type=float, default=200.0, help="Target segment length in meters")
    parser.add_argument("--target-count", type=int, default=10, help="Minimum number of demo segments to output")
    args = parser.parse_args()

    data = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    first = data["features"][0]
    coords: list[list[float]] = first["geometry"]["coordinates"]

    if len(coords) < 2:
        raise ValueError("Global route has insufficient coordinates")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    segments: list[dict] = []

    current = [coords[0]]
    current_dist = 0.0
    idx = 1

    for i in range(1, len(coords)):
        prev = coords[i - 1]
        cur = coords[i]
        d = haversine_m(prev[0], prev[1], cur[0], cur[1])

        current.append(cur)
        current_dist += d

        if current_dist >= args.segment_length_m:
            file_name = f"segment_{idx:03d}.gpx"
            write_gpx(OUTPUT_DIR / file_name, current, f"segment_{idx:03d}")
            segments.append({"id": idx, "file": file_name, "distance_m": round(current_dist, 2)})
            idx += 1
            current = [cur]
            current_dist = 0.0

    if len(current) > 1:
        file_name = f"segment_{idx:03d}.gpx"
        dist = line_distance_m(current)
        write_gpx(OUTPUT_DIR / file_name, current, f"segment_{idx:03d}")
        segments.append({"id": idx, "file": file_name, "distance_m": round(dist, 2)})

    while len(segments) < args.target_count:
        idx = len(segments) + 1
        file_name = f"segment_{idx:03d}.gpx"
        write_gpx(OUTPUT_DIR / file_name, [coords[0], coords[-1]], f"segment_{idx:03d}_duplicate_demo")
        segments.append({"id": idx, "file": file_name, "distance_m": round(line_distance_m([coords[0], coords[-1]]), 2)})

    MANIFEST_FILE.write_text(json.dumps({"segments": segments}, indent=2), encoding="utf-8")
    print(f"Generated {len(segments)} segments in {OUTPUT_DIR}")
    print(f"Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
