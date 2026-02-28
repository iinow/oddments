# Docker Benchmark Report (10M rows, HEAP=200m)

## Run config
- Runner: `run_docker_benchmark.sh`
- CPU: `1.0`
- Container memory: `1g`
- JVM heap: `-Xms200m -Xmx200m`
- Rows: `10,000,000`
- Output dir: `out/docker_10m_200m`

## Single-run benchmark results
- JsonNode
  - millis: `55,875`
  - rows/s: `178,970.92`
  - mem_delta_mb: `38.49`
- POJO
  - millis: `55,460`
  - rows/s: `180,310.13`
  - mem_delta_mb: `6.74`

### Quick compare
- Throughput: **POJO +0.75%** vs JsonNode
- Time: **POJO faster by ~415ms**

## GC detailed summary (from `gc_memory_detailed_summary.csv`)
- JsonNode
  - gc_events: `756`
  - gc_pause_sum_ms: `694.138`
  - gc_pause_max_ms: `37.735`
  - gc_pause_p95_ms: `0.720`
- POJO
  - gc_events: `459`
  - gc_pause_sum_ms: `325.488`
  - gc_pause_max_ms: `26.159`
  - gc_pause_p95_ms: `2.511`

## Chart
![gc_memory_detailed](./gc_memory_detailed.png)

## Artifacts
- `jsonnode.csv`
- `pojo.csv`
- `gc_memory_detailed_summary.csv`
- Heap dumps are generated in runtime output folder:
  - `out/docker_10m_200m/jsonnode.hprof`
  - `out/docker_10m_200m/pojo.hprof`
