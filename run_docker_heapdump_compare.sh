#!/usr/bin/env bash
set -euo pipefail

echo "[deprecated] use run_docker_benchmark.sh (integrated mode)"
DO_HEAPDUMP=true DO_ANALYZE=true ROWS="${ROWS:-10000000}" HEAP="${HEAP:-200m}" OUT_SUBDIR="${OUT_SUBDIR:-heapdump_docker}" CPU="${CPU:-1.0}" MEMORY="${MEMORY:-1g}" ./run_docker_benchmark.sh
