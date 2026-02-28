# Eclipse Memory Analyzer (MAT) Guide

## 1) Heap dump 생성 (자동)
프로젝트 루트에서:

```bash
./run_heapdump_compare.sh
```

기본 출력:
- `out/heapdump/jsonnode.hprof`
- `out/heapdump/pojo.hprof`
- `out/heapdump/gc_jsonnode.log`
- `out/heapdump/gc_pojo.log`

옵션 예시:

```bash
ROWS=10000000 HEAP=200m OUT_DIR=out/heapdump_10m ./run_heapdump_compare.sh
```

---

## 2) MAT에서 열기
1. Eclipse MAT 실행
2. `File -> Open Heap Dump`
3. `jsonnode.hprof`, `pojo.hprof` 각각 열기
4. "Leak Suspects" 자동 분석은 참고용으로만 보고, 아래 리포트를 우선 확인

---

## 3) 꼭 볼 리포트
- **Histogram**
  - 클래스별 객체 수 / shallow heap 비교
- **Dominator Tree**
  - retained heap 큰 루트 확인
- **Top Consumers**
  - 메모리 상위 점유 객체 파악

비교 포인트:
- `com.fasterxml.jackson.databind.node.*` 객체군(트리 노드)
- POJO 클래스(`Payload` 및 nested record)의 retained heap
- `char[]`, `byte[]`, `String` 비중

---

## 4) 발표용 체크리스트
- 동일 조건(같은 rows, heap, JDK)에서 dump 비교했는가?
- Full GC 타이밍 차이(실행 종료 직전)로 왜곡되지 않는가?
- GC 로그의 pause 합/p95/p99와 MAT 결과를 함께 제시했는가?

---

## 5) 자동 분석 리포트
- Macbook 수집본 분석: `out/BENCHMARK_ANALYSIS_MACBOOK_10M.md`
- 입력 원본: `out/macos_10m_5runs_input.txt`
