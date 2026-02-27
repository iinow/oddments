#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run_repeats_docker.sh [REPEATS]
# Example:
#   ./run_repeats_docker.sh 5

REPEATS="${1:-5}"
IMAGE_NAME="oddments-bench:latest"
OUT_DIR="$(pwd)/out/repeats"
mkdir -p "$OUT_DIR"

echo "[build] docker image -> $IMAGE_NAME"
docker build -t "$IMAGE_NAME" . >/dev/null

echo "[run] repeats=$REPEATS (cpu=1, mem=1g)"
for i in $(seq 1 "$REPEATS"); do
  OUT_CSV="/app/out/repeat_${i}.csv"
  echo "  - repeat #$i"
  docker run --rm \
    --cpus="1.0" \
    --memory="1g" \
    -v "$OUT_DIR:/app/out" \
    "$IMAGE_NAME" \
    --rows 1000000 \
    --data /app/out/payload_1m.ndjson \
    --out "$OUT_CSV" >/dev/null

done

echo "[done] CSVs: $OUT_DIR/repeat_*.csv"
echo "Next: python3 analyze_repeats.py --dir $OUT_DIR"
