#!/usr/bin/env bash
set -euo pipefail

ROWS="${ROWS:-10000000}"
HEAP="${HEAP:-200m}"
DATA="${DATA:-build/data/payload_java_10m.ndjson}"
OUT_DIR="${OUT_DIR:-out/heapdump}"

mkdir -p "$OUT_DIR"
mkdir -p "$(dirname "$DATA")"

# Compile if needed
javac -cp 'lib/*' -d build/classes src/main/java/com/oddments/bench/*.java

# Ensure data exists
java -Xms${HEAP} -Xmx${HEAP} -cp 'build/classes:lib/*' \
  com.oddments.bench.DeserializeBenchmarkApp \
  --mode jsonnode --rows "$ROWS" --data "$DATA" \
  --out "$OUT_DIR/_warmup_generate.csv" >/dev/null

# JsonNode with heap dump
java -Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file="$OUT_DIR/gc_jsonnode.log":time,uptime,level,tags \
  -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
  --mode jsonnode --rows "$ROWS" --data "$DATA" \
  --out "$OUT_DIR/jsonnode.csv" --heapDump "$OUT_DIR/jsonnode.hprof"

# POJO with heap dump
java -Xms${HEAP} -Xmx${HEAP} -Xlog:gc*,gc+heap=debug:file="$OUT_DIR/gc_pojo.log":time,uptime,level,tags \
  -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
  --mode pojo --rows "$ROWS" --data "$DATA" \
  --out "$OUT_DIR/pojo.csv" --heapDump "$OUT_DIR/pojo.hprof"

echo "Generated:"
echo "- $OUT_DIR/jsonnode.hprof"
echo "- $OUT_DIR/pojo.hprof"
echo "- $OUT_DIR/gc_jsonnode.log"
echo "- $OUT_DIR/gc_pojo.log"
