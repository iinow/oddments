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
docker run --rm \
  --cpus="$CPU" \
  --memory="$MEMORY" \
  -v "$OUT_DIR:/app/out" \
  "$IMAGE_NAME" \
  bash -lc "
    set -e
    # Ensure dataset for requested size
    java -Xms${HEAP} -Xmx${HEAP} -cp 'build/classes:lib/*' \
      com.oddments.bench.DeserializeBenchmarkApp \
      --mode jsonnode --rows ${ROWS} \
      --data /app/build/data/payload_java_${ROWS}.ndjson \
      --out /app/out/${OUT_SUBDIR}/_warmup_generate.csv >/dev/null

    # JsonNode
    java -Xms${HEAP} -Xmx${HEAP} \
      -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_jsonnode.log:time,uptime,level,tags \
      -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
      --mode jsonnode --rows ${ROWS} \
      --data /app/build/data/payload_java_${ROWS}.ndjson \
      --out /app/out/${OUT_SUBDIR}/jsonnode.csv \
      $( [ "$DO_HEAPDUMP" = "true" ] && echo "--heapDump /app/out/${OUT_SUBDIR}/jsonnode.hprof" )

    # POJO
    java -Xms${HEAP} -Xmx${HEAP} \
      -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_pojo.log:time,uptime,level,tags \
      -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
      --mode pojo --rows ${ROWS} \
      --data /app/build/data/payload_java_${ROWS}.ndjson \
      --out /app/out/${OUT_SUBDIR}/pojo.csv \
      $( [ "$DO_HEAPDUMP" = "true" ] && echo "--heapDump /app/out/${OUT_SUBDIR}/pojo.hprof" )
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
