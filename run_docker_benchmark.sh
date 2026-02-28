#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-oddments-bench:latest}"
OUT_DIR="${OUT_DIR:-$(pwd)/out}"
CPU="${CPU:-1.0}"
MEMORY="${MEMORY:-1g}"
ROWS="${ROWS:-1000000}"
HEAP="${HEAP:-200m}"
OUT_SUBDIR="${OUT_SUBDIR:-local_mac}"
DO_HEAPDUMP="${DO_HEAPDUMP:-true}"
DO_ANALYZE="${DO_ANALYZE:-true}"
DO_STATS="${DO_STATS:-true}"
DO_JFR="${DO_JFR:-true}"
JFR_SETTINGS="${JFR_SETTINGS:-profile}"
SAMPLE_SEC="${SAMPLE_SEC:-1}"

mkdir -p "$OUT_DIR/$OUT_SUBDIR"
rm -f "$OUT_DIR/$OUT_SUBDIR"/*

echo "[1/4] Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" . >/dev/null

APP_CMD="/app/oddments/bin/oddments"
DATA_PATH="/app/out/payload_java_${ROWS}.ndjson"

ensure_data() {
  docker run --rm --entrypoint bash \
    --cpus="$CPU" --memory="$MEMORY" \
    -v "$OUT_DIR:/app/out" \
    "$IMAGE_NAME" -lc "
      JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP}' ${APP_CMD} \
        --mode jsonnode --rows ${ROWS} --data ${DATA_PATH} \
        --out /app/out/${OUT_SUBDIR}/_warmup_generate.csv >/dev/null
    " >/dev/null
}

run_mode() {
  local mode="$1"
  local gc_log="/app/out/${OUT_SUBDIR}/gc_${mode}.log"
  local csv_out="/app/out/${OUT_SUBDIR}/${mode}.csv"
  local stats_csv="$OUT_DIR/$OUT_SUBDIR/${mode}_stats.csv"
  local heap_arg=""
  local jfr_opts=""

  if [ "$DO_HEAPDUMP" = "true" ]; then
    heap_arg="--heapDump /app/out/${OUT_SUBDIR}/${mode}.hprof"
  fi
  if [ "$DO_JFR" = "true" ]; then
    jfr_opts="-XX:StartFlightRecording=filename=/app/out/${OUT_SUBDIR}/${mode}.jfr,settings=${JFR_SETTINGS},dumponexit=true"
  fi

  local cid_file
  cid_file=$(mktemp)
  rm -f "$cid_file"
  trap 'rm -f "$cid_file"' RETURN

  docker run -d \
    --cidfile "$cid_file" \
    --entrypoint bash \
    --cpus="$CPU" --memory="$MEMORY" \
    -v "$OUT_DIR:/app/out" \
    "$IMAGE_NAME" -lc "
      JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file=${gc_log}:time,uptime,level,tags ${jfr_opts}' ${APP_CMD} \
        --mode ${mode} --rows ${ROWS} --data ${DATA_PATH} --out ${csv_out} ${heap_arg}
    " >/dev/null

  local cid
  cid=$(cat "$cid_file")

  if [ "$DO_STATS" = "true" ]; then
    echo "ts,cpu,mem_used_mb,mem_limit_mb" > "$stats_csv"
    while docker ps -q --no-trunc | grep -q "$cid"; do
      ts=$(date +%s)
      line=$(docker stats --no-stream --format '{{.CPUPerc}},{{.MemUsage}}' "$cid" | head -n1 || true)
      if [ -n "$line" ]; then
        cpu=$(echo "$line" | cut -d',' -f1)
        mem=$(echo "$line" | cut -d',' -f2)
        used=$(echo "$mem" | awk -F' / ' '{print $1}')
        limit=$(echo "$mem" | awk -F' / ' '{print $2}')
        used_mb=$(echo "$used" | awk '{gsub(/ /,""); if($0 ~ /KiB$/){sub(/KiB$/,""); printf "%.2f", $0/1024} else if($0 ~ /MiB$/){sub(/MiB$/,""); printf "%.2f", $0} else if($0 ~ /GiB$/){sub(/GiB$/,""); printf "%.2f", $0*1024} else if($0 ~ /TiB$/){sub(/TiB$/,""); printf "%.2f", $0*1024*1024} else {printf "0.00"}}')
        limit_mb=$(echo "$limit" | awk '{gsub(/ /,""); if($0 ~ /KiB$/){sub(/KiB$/,""); printf "%.2f", $0/1024} else if($0 ~ /MiB$/){sub(/MiB$/,""); printf "%.2f", $0} else if($0 ~ /GiB$/){sub(/GiB$/,""); printf "%.2f", $0*1024} else if($0 ~ /TiB$/){sub(/TiB$/,""); printf "%.2f", $0*1024*1024} else {printf "0.00"}}')
        echo "$ts,$cpu,$used_mb,$limit_mb" >> "$stats_csv"
      fi
      sleep "$SAMPLE_SEC"
    done
  fi

  code=$(docker wait "$cid")
  if [ "$code" != "0" ]; then
    echo "container failed (${mode}) code=$code"
    docker logs "$cid" || true
    exit 1
  fi

  rm -f "$cid_file"
  trap - RETURN
}

echo "[2/4] Preparing dataset"
ensure_data

echo "[3/4] Running JsonNode + POJO separately"
run_mode jsonnode
run_mode pojo

if [ "$DO_ANALYZE" = "true" ]; then
  echo "[4/4] Generating analysis artifacts"
  python3 plot_gc_memory_detailed.py \
    --jsonnode-gc "$OUT_DIR/$OUT_SUBDIR/gc_jsonnode.log" \
    --pojo-gc "$OUT_DIR/$OUT_SUBDIR/gc_pojo.log" \
    --jsonnode-csv "$OUT_DIR/$OUT_SUBDIR/jsonnode.csv" \
    --pojo-csv "$OUT_DIR/$OUT_SUBDIR/pojo.csv" \
    --out-png "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed.png" \
    --out-summary "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed_summary.csv"
fi

if [ "$DO_STATS" = "true" ]; then
  python3 plot_docker_stats.py \
    --jsonnode "$OUT_DIR/$OUT_SUBDIR/jsonnode_stats.csv" \
    --pojo "$OUT_DIR/$OUT_SUBDIR/pojo_stats.csv" \
    --out "$OUT_DIR/$OUT_SUBDIR/docker_cpu_mem_chart_compare.png"
fi

REPORT_DIR="$(pwd)/reports/$OUT_SUBDIR"
mkdir -p "$REPORT_DIR"
cp -f "$OUT_DIR/$OUT_SUBDIR/jsonnode.csv" "$REPORT_DIR/jsonnode.csv"
cp -f "$OUT_DIR/$OUT_SUBDIR/pojo.csv" "$REPORT_DIR/pojo.csv"
cp -f "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed_summary.csv" "$REPORT_DIR/gc_memory_detailed_summary.csv"
cp -f "$OUT_DIR/$OUT_SUBDIR/gc_memory_detailed.png" "$REPORT_DIR/gc_memory_detailed.png"
if [ "$DO_STATS" = "true" ]; then
  cp -f "$OUT_DIR/$OUT_SUBDIR/jsonnode_stats.csv" "$REPORT_DIR/jsonnode_stats.csv"
  cp -f "$OUT_DIR/$OUT_SUBDIR/pojo_stats.csv" "$REPORT_DIR/pojo_stats.csv"
  cp -f "$OUT_DIR/$OUT_SUBDIR/docker_cpu_mem_chart_compare.png" "$REPORT_DIR/docker_cpu_mem_chart_compare.png"
fi
if [ "$DO_JFR" = "true" ]; then
  cp -f "$OUT_DIR/$OUT_SUBDIR/jsonnode.jfr" "$REPORT_DIR/jsonnode.jfr" || true
  cp -f "$OUT_DIR/$OUT_SUBDIR/pojo.jfr" "$REPORT_DIR/pojo.jfr" || true
fi

python3 generate_docker_report.py --out-subdir "$OUT_SUBDIR" --out-root "$OUT_DIR" --reports-root "$(pwd)/reports"

echo "Done. Output dir: $OUT_DIR/$OUT_SUBDIR"
if [ "$DO_JFR" = "true" ]; then
  echo "- jsonnode.jfr"
  echo "- pojo.jfr"
fi
