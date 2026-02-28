# Docker Benchmark Report (docker_10m_200m)

## Single-run benchmark results

- JsonNode: 30644 ms, 326328.16 rows/s, mem_delta=38.49 MB
- POJO: 29666 ms, 337086.23 rows/s, mem_delta=6.74 MB

- Throughput compare: **POJO +3.30%** vs JsonNode
- Time compare: **POJO faster by 978 ms**

## GC summary

- JsonNode: events=756, pause_sum=515.94 ms, pause_max=15.91 ms, pause_p95=0.68 ms
- POJO: events=459, pause_sum=252.27 ms, pause_max=18.38 ms, pause_p95=0.45 ms

## Container CPU/Memory stats (mode-separated)

- JsonNode samples: 13, CPU avg/peak: **92.84% / 102.99%**, Mem avg/peak: **84.24 / 92.45 MB**
- POJO samples: 13, CPU avg/peak: **92.91% / 104.06%**, Mem avg/peak: **86.45 / 94.70 MB**

## Charts

![gc_memory_detailed](./gc_memory_detailed.png)
![docker_cpu_mem_chart_compare](./docker_cpu_mem_chart_compare.png)