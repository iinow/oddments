# Benchmark Analysis (Auto)

## Summary
- Samples per mode: **5**
- Checksum consistency: **OK**

### JsonNode (mean ± std)
- millis: **16927.8 ± 263.0 ms**
- rows/s: **590886.83 ± 9178.52**
- mem_delta_mb: **0.91 ± 0.66**

### POJO (mean ± std)
- millis: **14942.6 ± 407.9 ms**
- rows/s: **669717.86 ± 17965.49**
- mem_delta_mb: **-0.24 ± 1.12**

## Interpretation
- Throughput: **POJO +13.34%** vs JsonNode
- Time-to-complete: **POJO 13.29% faster** (lower millis)
- `mem_delta_mb` can be noisy (snapshot delta), so use GC logs/heap dump for memory conclusions.

## Recommendation
- On this machine/run set, **POJO is clearly faster**.
- For memory, use MAT comparison on `.hprof` + GC log metrics (pause sum/p95/p99).
