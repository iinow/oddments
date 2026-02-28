# oddments - JsonNode vs POJO 역직렬화 벤치마크

Spring/Jackson 환경에서 중첩 JSON(깊이 6) 역직렬화 시 `JsonNode`와 `POJO`를 비교하기 위한 샘플입니다.

## 왜 이 코드를 만들었나
- 역직렬화 병목이 CPU인지, 메모리인지 논쟁이 있을 때
- "생각" 말고 수치로 확인하고 싶을 때
- 제한된 자원(CPU/메모리)에서 상대 차이를 보고 싶을 때

## 실행 (Docker 권장: 벤치 + GC로그 + 힙덤프 + 분석)
```bash
cd ~/.clawdbot/projects/oddments
ROWS=10000000 HEAP=200m OUT_SUBDIR=docker_10m ./run_docker_benchmark.sh
```

기본 조건(환경변수로 변경 가능):
- CPU: 1 core (`CPU=1.0`)
- Memory: 1GB (`MEMORY=1g`)
- Heap: `HEAP=200m`
- Rows: `ROWS=1000000`
- Heapdump on/off: `DO_HEAPDUMP=true|false`
- 분석 산출물 on/off: `DO_ANALYZE=true|false`

직접 실행하고 싶으면:
```bash
docker build -t oddments-bench:latest .
docker run --rm --cpus="1.0" --memory="1g" \
  -v "$(pwd)/out:/app/out" oddments-bench:latest
```

앱 옵션(CMD 인자):
- `--rows` : 생성/처리 레코드 수 (기본 1,000,000)
- `--data` : NDJSON 파일 경로
- `--out` : 결과 CSV 경로

## 결과
CSV 예시 컬럼:
- mode (`JsonNode` / `POJO`)
- rows
- millis
- rows_per_sec
- mem_before_mb / mem_after_mb / mem_delta_mb
- checksum

## 차트(옵션)
```bash
python3 -m pip install matplotlib
python3 plot.py
```

생성 파일:
- `build/reports/deserialize_benchmark.png`

## 자동 분석 리포트 생성 (Markdown)
```bash
./analyze_benchmark_to_md.py --input out/macos_10m_5runs_input.txt --out out/BENCHMARK_ANALYSIS_MACBOOK_10M.md
```

## Heap dump 자동 생성 + MAT 준비
### Docker 실행에서 직접 추출 (권장)
```bash
ROWS=10000000 HEAP=200m OUT_SUBDIR=heapdump_docker ./run_docker_heapdump_compare.sh
```

### 호스트 Java로 추출 (옵션)
```bash
./run_heapdump_compare.sh
```

생성 파일:
- `out/<OUT_SUBDIR>/jsonnode.hprof`
- `out/<OUT_SUBDIR>/pojo.hprof`
- `out/<OUT_SUBDIR>/gc_jsonnode.log`
- `out/<OUT_SUBDIR>/gc_pojo.log`
- 가이드: `out/MAT_HEAPDUMP_GUIDE.md`

## 해석 팁
- 이 샘플은 "절대 성능"보다 "상대 비교"용입니다.
- GC/JVM옵션/CPU 상태/파일 캐시 상태에 따라 값이 바뀝니다.
- 실무 판단은 실제 payload 스키마/필드 수/문자열 길이로 재현하는 게 정확합니다.
