package com.oddments.bench;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.management.HotSpotDiagnosticMXBean;
import org.simdjson.SimdJsonParser;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public class DeserializeBenchmarkApp {
    private static final ObjectMapper MAPPER = new ObjectMapper();
    // SimdJsonParser is created lazily in runSimdJson().

    public static void main(String[] args) throws Exception {
        int rows = intArg(args, "--rows", 1_000_000);
        Path dataPath = Path.of(strArg(args, "--data", "build/data/payload.ndjson"));
        Path outCsv = Path.of(strArg(args, "--out", "build/reports/deserialize_benchmark.csv"));

        Files.createDirectories(dataPath.getParent());
        Files.createDirectories(outCsv.getParent());

        if (!Files.exists(dataPath)) {
            System.out.println("[1/3] Generating test NDJSON: " + dataPath + " (rows=" + rows + ")");
            generate(rows, dataPath);
        } else {
            System.out.println("[1/3] Reusing existing NDJSON: " + dataPath);
        }

        String mode = strArg(args, "--mode", "both").toLowerCase(Locale.ROOT);
        String heapDump = strArg(args, "--heapDump", "");

        System.out.println("[2/3] Warm-up... mode=" + mode);
        switch (mode) {
            case "jsonnode" -> runJsonNode(dataPath, 50_000);
            case "pojo" -> runPojo(dataPath, 50_000);
            case "simdjson" -> runSimdJson(dataPath, 50_000);
            default -> {
                runJsonNode(dataPath, 50_000);
                runPojo(dataPath, 50_000);
                runSimdJson(dataPath, 50_000);
            }
        }

        System.out.println("[3/3] Benchmarking full file...");
        List<Result> results = new ArrayList<>();
        switch (mode) {
            case "jsonnode" -> results.add(runJsonNode(dataPath, Integer.MAX_VALUE));
            case "pojo" -> results.add(runPojo(dataPath, Integer.MAX_VALUE));
            case "simdjson" -> results.add(runSimdJson(dataPath, Integer.MAX_VALUE));
            default -> {
                results.add(runJsonNode(dataPath, Integer.MAX_VALUE));
                results.add(runPojo(dataPath, Integer.MAX_VALUE));
                results.add(runSimdJson(dataPath, Integer.MAX_VALUE));
            }
        }

        writeCsv(outCsv, results.toArray(Result[]::new));
        printSummary(results, outCsv);

        if (!heapDump.isBlank()) {
            dumpHeap(heapDump);
            System.out.println("Heap dump saved: " + heapDump);
        }
    }

    private static int intArg(String[] args, String key, int def) {
        for (int i = 0; i < args.length - 1; i++) {
            if (args[i].equals(key)) return Integer.parseInt(args[i + 1]);
        }
        return def;
    }

    private static String strArg(String[] args, String key, String def) {
        for (int i = 0; i < args.length - 1; i++) {
            if (args[i].equals(key)) return args[i + 1];
        }
        return def;
    }

    private static void generate(int rows, Path path) throws IOException {
        Random random = new Random(42);
        try (BufferedWriter bw = Files.newBufferedWriter(path)) {
            for (int i = 0; i < rows; i++) {
                String json = sampleJson(i, random);
                bw.write(json);
                bw.newLine();
            }
        }
    }

    private static String sampleJson(int i, Random random) {
        return String.format(Locale.US,
                "{\"id\":\"item-%d\",\"ts\":%d,\"type\":\"event\",\"value\":%d," +
                        "\"nested\":{\"name\":\"l1\",\"score\":%d,\"child\":{" +
                        "\"name\":\"l2\",\"score\":%d,\"child\":{" +
                        "\"name\":\"l3\",\"score\":%d,\"child\":{" +
                        "\"name\":\"l4\",\"score\":%d,\"child\":{" +
                        "\"name\":\"l5\",\"score\":%d,\"child\":{" +
                        "\"name\":\"l6\",\"score\":%d,\"leaf\":\"hello-%d\"}}}}}}}",
                i,
                System.currentTimeMillis() + i,
                random.nextInt(10_000),
                random.nextInt(100),
                random.nextInt(100),
                random.nextInt(100),
                random.nextInt(100),
                random.nextInt(100),
                random.nextInt(100),
                i
        );
    }

    private static Result runJsonNode(Path path, int maxRows) throws IOException {
        long memBefore = usedMem();
        Instant start = Instant.now();
        long checksum = 0;
        int count = 0;

        try (BufferedReader br = Files.newBufferedReader(path)) {
            String line;
            while ((line = br.readLine()) != null && count < maxRows) {
                JsonNode node = MAPPER.readTree(line);
                checksum += node.get("value").asInt();
                checksum += node.path("nested").path("child").path("child").path("child")
                        .path("child").path("child").path("score").asInt();
                count++;
            }
        }

        long millis = Duration.between(start, Instant.now()).toMillis();
        long memAfter = usedMem();
        return new Result("JsonNode", count, millis, memBefore, memAfter, checksum);
    }

    private static Result runPojo(Path path, int maxRows) throws IOException {
        long memBefore = usedMem();
        Instant start = Instant.now();
        long checksum = 0;
        int count = 0;

        try (BufferedReader br = Files.newBufferedReader(path)) {
            String line;
            while ((line = br.readLine()) != null && count < maxRows) {
                Payload p = MAPPER.readValue(line, Payload.class);
                checksum += p.value();
                checksum += p.nested().child().child().child().child().child().score();
                count++;
            }
        }

        long millis = Duration.between(start, Instant.now()).toMillis();
        long memAfter = usedMem();
        return new Result("POJO", count, millis, memBefore, memAfter, checksum);
    }

    private static Result runSimdJson(Path path, int maxRows) throws IOException {
        long memBefore = usedMem();
        Instant start = Instant.now();
        long checksum = 0;
        int count = 0;
        SimdJsonParser simd = new SimdJsonParser(1 << 20, 128);

        try (BufferedReader br = Files.newBufferedReader(path)) {
            String line;
            while ((line = br.readLine()) != null && count < maxRows) {
                byte[] bytes = line.getBytes(StandardCharsets.UTF_8);
                Payload p = simd.parse(bytes, bytes.length, Payload.class);
                checksum += p.value();
                checksum += p.nested().child().child().child().child().child().score();
                count++;
            }
        }

        long millis = Duration.between(start, Instant.now()).toMillis();
        long memAfter = usedMem();
        return new Result("SimdJson", count, millis, memBefore, memAfter, checksum);
    }

    private static long usedMem() {
        Runtime rt = Runtime.getRuntime();
        return rt.totalMemory() - rt.freeMemory();
    }

    private static void dumpHeap(String path) {
        try {
            Path p = Path.of(path);
            Files.createDirectories(p.getParent());
            HotSpotDiagnosticMXBean mxBean = ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class);
            mxBean.dumpHeap(path, true);
        } catch (Exception e) {
            throw new RuntimeException("Failed to dump heap: " + path, e);
        }
    }

    private static void writeCsv(Path outCsv, Result... results) throws IOException {
        try (BufferedWriter bw = Files.newBufferedWriter(outCsv)) {
            bw.write("mode,rows,millis,rows_per_sec,mem_before_mb,mem_after_mb,mem_delta_mb,checksum");
            bw.newLine();
            for (Result r : results) {
                bw.write(r.toCsv());
                bw.newLine();
            }
        }
    }

    private static void printSummary(List<Result> results, Path outCsv) {
        System.out.println("\n===== RESULT =====");
        for (Result r : results) {
            System.out.printf(Locale.US, "%s: %d ms, %.2f rows/s, Δmem=%.2f MB%n",
                    r.mode, r.millis, r.rowsPerSec(), r.memDeltaMb());
        }
        System.out.println("CSV saved: " + outCsv);
    }

    private record Result(String mode, int rows, long millis, long memBefore, long memAfter, long checksum) {
        double rowsPerSec() {
            return rows / (millis / 1000.0);
        }

        double memDeltaMb() {
            return (memAfter - memBefore) / (1024.0 * 1024.0);
        }

        String toCsv() {
            return String.format(Locale.US,
                    "%s,%d,%d,%.2f,%.2f,%.2f,%.2f,%d",
                    mode, rows, millis, rowsPerSec(),
                    memBefore / (1024.0 * 1024.0),
                    memAfter / (1024.0 * 1024.0),
                    memDeltaMb(), checksum);
        }
    }
}
