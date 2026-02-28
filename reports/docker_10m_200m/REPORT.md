# Docker Benchmark Report (docker_10m_200m)

## Single-run benchmark results

- JsonNode: 30737 ms, 325340.79 rows/s, mem_delta=38.49 MB
- POJO: 30053 ms, 332745.48 rows/s, mem_delta=6.46 MB

- Throughput compare: **POJO +2.28%** vs JsonNode
- Time compare: **POJO faster by 684 ms**

## GC summary

- JsonNode: events=756, pause_sum=522.35 ms, pause_max=26.31 ms, pause_p95=0.73 ms
- POJO: events=459, pause_sum=310.70 ms, pause_max=45.47 ms, pause_p95=0.50 ms

## Container CPU/Memory stats

- samples: 40
- CPU avg: **93.14%**, CPU peak: **104.11%**
- Mem avg: **0.00 MB**, Mem peak: **0.00 MB**

## Charts

![gc_memory_detailed](./gc_memory_detailed.png)
![docker_cpu_mem_chart](./docker_cpu_mem_chart.png)