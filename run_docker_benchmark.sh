#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-oddments-bench:latest}"
OUT_DIR="${OUT_DIR:-$(pwd)/out}"
CPU="${CPU:-1.0}"
MEMORY="${MEMORY:-1g}"
ROWS="${ROWS:-1000000}"
HEAP="${HEAP:-200m}"
OUT_SUBDIR="${OUT_SUBDIR:-docker_bench}"
DO_HEAPDUMP="${DO_HEAPDUMP:-true}"
DO_ANALYZE="${DO_ANALYZE:-true}"

mkdir -p "$OUT_DIR/$OUT_SUBDIR"

echo "[1/3] Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

echo "[2/3] Running benchmark in constrained container (CPU=$CPU / MEM=$MEMORY, rows=$ROWS)"
HEAPDUMP_JSON=""
HEAPDUMP_POJO=""
if [ "$DO_HEAPDUMP" = "true" ]; then
  HEAPDUMP_JSON="--heapDump /app/out/${OUT_SUBDIR}/jsonnode.hprof"
  HEAPDUMP_POJO="--heapDump /app/out/${OUT_SUBDIR}/pojo.hprof"
fi

docker run --rm \
  --entrypoint bash \
  --cpus="$CPU" \
  --memory="$MEMORY" \
  -v "$OUT_DIR:/app/out" \
  "$IMAGE_NAME" \
  -lc "
    set -e
    APP=/app/oddments/bin/oddments
    DATA=/app/out/payload_java_${ROWS}.ndjson

    # ensure dataset exists
    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP}' \"\$APP\" \
      --mode jsonnode --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/_warmup_generate.csv >/dev/null

    # JsonNode run
    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_jsonnode.log:time,uptime,level,tags' \"\$APP\" \
      --mode jsonnode --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/jsonnode.csv ${HEAPDUMP_JSON}

    # POJO run
    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_pojo.log:time,uptime,level,tags' \"\$APP\" \
      --mode pojo --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/pojo.csv ${HEAPDUMP_POJO}
  "

if [ "$DO_ANALYZE" = "true" ]; then
  echo "[3/3] Generating detailed analysis artifacts"
  python3 plot_gc_memory_detailed.py \
    --jsonnode-gc "$OUT_DIR/$OUT_SUBDIR/gc_jsonnode.log" \
    --pojo-gc "$OUT_DIR/$OUT_SUBDIR/gc_pojo.log" \
    --jsonnode-csv "$OUT_DIR/$OUT_SUBDIR/jsonnode.csv" \
    --pojo-csv "$OUT_DIR/$OUT_SUBDIR/pojo.csv" \
    --out-png "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed.png" \
    --out-summary "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed_summary.csv"
fi

echo "Done. Output dir: $OUT_DIR/$OUT_SUBDIR"
echo "- jsonnode.csv"
echo "- pojo.csv"
echo "- gc_jsonnode.log"
echo "- gc_pojo.log"
if [ "$DO_HEAPDUMP" = "true" ]; then
  echo "- jsonnode.hprof"
  echo "- pojo.hprof"
fi
if [ "$DO_ANALYZE" = "true" ]; then
  echo "- gc_memory_detailed.png"
  echo "- gc_memory_detailed_summary.csv"
fi
