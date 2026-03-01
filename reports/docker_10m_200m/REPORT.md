# Docker Benchmark Report (docker_10m_200m)

## Single-run benchmark results

- JsonNode: 31822 ms, 314248.00 rows/s, mem_delta=-11.23 MB
- POJO: 30324 ms, 329771.80 rows/s, mem_delta=8.77 MB
- SimdJson: 472170 ms, 21178.81 rows/s, mem_delta=21.52 MB

- Throughput compare: **POJO +4.94%** vs JsonNode
- Time compare: **POJO faster by 1498 ms**
- SimdJson throughput vs JsonNode: **-93.26%**
- SimdJson throughput vs POJO: **-93.58%**

## GC summary

- JsonNode: events=757, pause_sum=600.60 ms, pause_max=60.29 ms, pause_p95=0.77 ms
- POJO: events=460, pause_sum=233.71 ms, pause_max=30.39 ms, pause_p95=0.54 ms

## Container CPU/Memory stats (mode-separated)

- JsonNode samples: 14, CPU avg/peak: **93.43% / 103.06%**, Mem avg/peak: **94.98 / 107.20 MB**
- POJO samples: 13, CPU avg/peak: **100.38% / 102.91%**, Mem avg/peak: **104.55 / 109.40 MB**
- SimdJson samples: 186, CPU avg/peak: **99.77% / 102.87%**, Mem avg/peak: **157.42 / 161.30 MB**

## Charts

![gc_memory_detailed](./gc_memory_detailed.png)
![docker_cpu_mem_chart_compare](./docker_cpu_mem_chart_compare.png)

## JFR files

- jsonnode.jfr
- pojo.jfr
- simdjson.jfr