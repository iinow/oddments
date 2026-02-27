# oddments - JsonNode vs POJO 역직렬화 벤치마크

Spring/Jackson 환경에서 중첩 JSON(깊이 6) 역직렬화 시 `JsonNode`와 `POJO`를 비교하기 위한 샘플입니다.

## 왜 이 코드를 만들었나
- 역직렬화 병목이 CPU인지, 메모리인지 논쟁이 있을 때
- "생각" 말고 수치로 확인하고 싶을 때
- 제한된 자원(CPU/메모리)에서 상대 차이를 보고 싶을 때

## 실행
```bash
cd ~/.clawdbot/projects/oddments
./gradlew run --args="--rows 1000000"
```

옵션:
- `--rows` : 생성/처리 레코드 수 (기본 1,000,000)
- `--data` : NDJSON 파일 경로 (기본 `build/data/payload.ndjson`)
- `--out` : 결과 CSV (기본 `build/reports/deserialize_benchmark.csv`)

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

## 해석 팁
- 이 샘플은 "절대 성능"보다 "상대 비교"용입니다.
- GC/JVM옵션/CPU 상태/파일 캐시 상태에 따라 값이 바뀝니다.
- 실무 판단은 실제 payload 스키마/필드 수/문자열 길이로 재현하는 게 정확합니다.
