#!/usr/bin/env bash
set -euo pipefail

ROWS="${ROWS:-10000000}"
HEAP="${HEAP:-200m}"
CPU="${CPU:-1.0}"
MEMORY="${MEMORY:-1g}"
OUT_SUBDIR="${OUT_SUBDIR:-heapdump_docker}"

mkdir -p "out/${OUT_SUBDIR}"

docker build -t oddments-bench:latest .

docker run --rm \
  --cpus="${CPU}" \
  --memory="${MEMORY}" \
  -v "$(pwd)/out:/app/out" \
  oddments-bench:latest \
  bash -lc "
    java -Xms${HEAP} -Xmx${HEAP} \
      -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_jsonnode.log:time,uptime,level,tags \
      -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
      --mode jsonnode --preGc false --rows ${ROWS} \
      --data /app/build/data/payload_java_${ROWS}.ndjson \
      --out /app/out/${OUT_SUBDIR}/jsonnode.csv \
      --heapDump /app/out/${OUT_SUBDIR}/jsonnode.hprof

    java -Xms${HEAP} -Xmx${HEAP} \
      -Xlog:gc*,gc+heap=debug:file=/app/out/${OUT_SUBDIR}/gc_pojo.log:time,uptime,level,tags \
      -cp 'build/classes:lib/*' com.oddments.bench.DeserializeBenchmarkApp \
      --mode pojo --preGc false --rows ${ROWS} \
      --data /app/build/data/payload_java_${ROWS}.ndjson \
      --out /app/out/${OUT_SUBDIR}/pojo.csv \
      --heapDump /app/out/${OUT_SUBDIR}/pojo.hprof
  "

echo "Generated in out/${OUT_SUBDIR}:"
echo "- jsonnode.hprof"
echo "- pojo.hprof"
echo "- gc_jsonnode.log"
echo "- gc_pojo.log"
