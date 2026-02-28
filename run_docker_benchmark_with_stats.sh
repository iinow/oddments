#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-oddments-bench:latest}"
OUT_DIR="${OUT_DIR:-$(pwd)/out}"
CPU="${CPU:-1.0}"
MEMORY="${MEMORY:-1g}"
ROWS="${ROWS:-10000000}"
HEAP="${HEAP:-200m}"
OUT_SUBDIR="${OUT_SUBDIR:-docker_10m_200m_stats}"
SAMPLE_SEC="${SAMPLE_SEC:-1}"

mkdir -p "$OUT_DIR/$OUT_SUBDIR"

echo "[1/4] docker build"
docker build -t "$IMAGE_NAME" . >/dev/null

cid_file=$(mktemp)
trap 'rm -f "$cid_file"' EXIT

echo "[2/4] run container detached"
docker run -d \
  --cidfile "$cid_file" \
  --entrypoint bash \
  --cpus="$CPU" \
  --memory="$MEMORY" \
  -v "$OUT_DIR:/app/out" \
  "$IMAGE_NAME" \
  -lc "
    set -e
    APP=/app/oddments/bin/oddments
    DATA=/app/out/payload_java_${ROWS}.ndjson

    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP}' \"\$APP\" --mode jsonnode --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/_warmup_generate.csv >/dev/null
    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_jsonnode.log:time,uptime,level,tags' \"\$APP\" --mode jsonnode --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/jsonnode.csv
    JAVA_TOOL_OPTIONS='-Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_pojo.log:time,uptime,level,tags' \"\$APP\" --mode pojo --rows ${ROWS} --data \"\$DATA\" --out /app/out/${OUT_SUBDIR}/pojo.csv
  " >/dev/null

CID=$(cat "$cid_file")
STATS_CSV="$OUT_DIR/$OUT_SUBDIR/docker_stats.csv"
echo "ts,cpu,mem_used_mb,mem_limit_mb" > "$STATS_CSV"

echo "[3/4] sampling docker stats"
while docker ps -q --no-trunc | grep -q "$CID"; do
  ts=$(date +%s)
  line=$(docker stats --no-stream --format '{{.CPUPerc}},{{.MemUsage}}' "$CID" | head -n1 || true)
  if [ -n "$line" ]; then
    cpu=$(echo "$line" | cut -d',' -f1)
    mem=$(echo "$line" | cut -d',' -f2)
    used=$(echo "$mem" | awk -F' / ' '{print $1}')
    limit=$(echo "$mem" | awk -F' / ' '{print $2}')
    used_mb=$(numfmt --from=iec "$used" 2>/dev/null | awk '{printf "%.2f", $1/1024/1024}' || echo "0")
    limit_mb=$(numfmt --from=iec "$limit" 2>/dev/null | awk '{printf "%.2f", $1/1024/1024}' || echo "0")
    echo "$ts,$cpu,$used_mb,$limit_mb" >> "$STATS_CSV"
  fi
  sleep "$SAMPLE_SEC"
done

# ensure container completed successfully
code=$(docker wait "$CID")
if [ "$code" != "0" ]; then
  echo "container failed with code $code"
  docker logs "$CID" || true
  exit 1
fi

echo "[4/4] plotting cpu/mem chart"
python3 plot_docker_stats.py --input "$STATS_CSV" --out "$OUT_DIR/$OUT_SUBDIR/docker_cpu_mem_chart.png"

echo "Done: $OUT_DIR/$OUT_SUBDIR"
