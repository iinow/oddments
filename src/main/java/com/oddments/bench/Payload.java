package com.oddments.bench;

public record Payload(
        String id,
        long ts,
        String type,
        int value,
        L1 nested
) {
    public record L1(String name, int score, L2 child) {}
    public record L2(String name, int score, L3 child) {}
    public record L3(String name, int score, L4 child) {}
    public record L4(String name, int score, L5 child) {}
    public record L5(String name, int score, L6 child) {}
    public record L6(String name, int score, String leaf) {}
}
