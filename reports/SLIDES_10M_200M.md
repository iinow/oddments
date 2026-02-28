# Slide 1 — JsonNode vs POJO (10M, 200MB)

- 목적: Jackson 역직렬화 방식 비교 (성능 + GC)
- 대상: `JsonNode` vs `POJO`
- 데이터: NDJSON, nested depth 6, **10,000,000 rows**
- JVM: OpenJDK 21
- 힙: `-Xms200m -Xmx200m`
- 반복: 모드별 **5회 분리 실행** (``)

---

# Slide 2 — 실험 설계

- 로그: `-Xlog:gc*,gc+heap=debug`
- 측정 지표
  - Throughput (`rows/s`)
  - 실행시간 (`millis`)
  - GC events
  - STW pause (sum / max / p95 / p99)
- 산출물
  - `repeat_10m_200m_nopregc_summary.csv`
  - `repeat_10m_200m_nopregc_overview.png`
  - `gc_memory_detailed_10m_200m.png`

---

# Slide 3 — 핵심 결과 (5회 평균)

## JsonNode
- Throughput: **324,832 rows/s**
- Time: **30,785.8 ms**
- GC events: **341.0**
- GC pause sum: **363.2 ms**
- GC pause max: **4.61 ms**

## POJO
- Throughput: **320,451 rows/s**
- Time: **31,206.6 ms**
- GC events: **208.0**
- GC pause sum: **207.0 ms**
- GC pause max: **4.76 ms**

---

# Slide 4 — 시각화

## Repeat overview

![repeat-overview](./repeat_10m_200m_nopregc_overview.png)

## Detailed GC/Memory snapshot

![gc-detailed](./gc_memory_detailed_10m_200m.png)

---

# Slide 5 — 결론 / 의사결정 가이드

- 처리량 기준: **JsonNode 소폭 우세** (약 +1.37%)
- GC 누적 STW 기준: **POJO 우세** (pause sum 약 -43%)
- 최대 STW는 반복 측정에서 유사한 범위

### 선택 기준
- **TPS/지연시간 우선**: JsonNode
- **GC 부담/안정성 우선**: POJO

### 권장 후속
- 실제 서비스 payload로 동일 프로토콜 재검증
- p99 latency + CPU 사용률까지 합쳐 최종 결정
