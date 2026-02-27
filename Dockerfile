# syntax=docker/dockerfile:1.7

# ----- build stage -----
FROM gradle:8.10.2-jdk21 AS builder
WORKDIR /app

COPY build.gradle settings.gradle ./
COPY src ./src

# Build a runnable distribution (includes start scripts + libs)
RUN gradle --no-daemon clean installDist

# ----- runtime stage -----
FROM eclipse-temurin:21-jre
WORKDIR /app

COPY --from=builder /app/build/install/oddments ./oddments

# default: run benchmark with 1,000,000 rows
ENTRYPOINT ["/app/oddments/bin/oddments"]
CMD ["--rows", "1000000", "--data", "/app/out/payload_1m.ndjson", "--out", "/app/out/deserialize_benchmark_java_1m.csv"]
