#!/usr/bin/env bash
set -euo pipefail

mkdir -p apps/web/public/gpx
cp artifacts/gpx/segments_manifest.json apps/web/public/segments_manifest.json
cp artifacts/gpx/segment_*.gpx apps/web/public/gpx/
