# Docker Benchmark Report (docker_10m_200m_cpu2)

## Single-run benchmark results

- JsonNode: 30207 ms, 331049.09 rows/s, mem_delta=38.49 MB
- POJO: 29445 ms, 339616.23 rows/s, mem_delta=6.74 MB

- Throughput compare: **POJO +2.59%** vs JsonNode
- Time compare: **POJO faster by 762 ms**

## GC summary

- JsonNode: events=756, pause_sum=501.92 ms, pause_max=16.32 ms, pause_p95=0.67 ms
- POJO: events=459, pause_sum=251.54 ms, pause_max=17.59 ms, pause_p95=0.45 ms

## Container CPU/Memory stats (mode-separated)

- JsonNode samples: 13, CPU avg/peak: **97.31% / 161.13%**, Mem avg/peak: **83.94 / 92.68 MB**
- POJO samples: 12, CPU avg/peak: **105.42% / 159.46%**, Mem avg/peak: **93.92 / 94.46 MB**

## Charts

![gc_memory_detailed](./gc_memory_detailed.png)
![docker_cpu_mem_chart_compare](./docker_cpu_mem_chart_compare.png)