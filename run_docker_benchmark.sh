#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="oddments-bench:latest"
OUT_DIR="$(pwd)/out"

mkdir -p "$OUT_DIR"

echo "[1/2] Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

echo "[2/2] Running benchmark in constrained container (1 CPU / 1GB RAM)"
docker run --rm \
  --cpus="1.0" \
  --memory="1g" \
  -v "$OUT_DIR:/app/out" \
  "$IMAGE_NAME"

echo "Done. Check: $OUT_DIR/deserialize_benchmark_java_1m.csv"
