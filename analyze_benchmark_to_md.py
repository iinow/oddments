#!/usr/bin/env python3
import argparse
import csv
import re
import statistics
from pathlib import Path

LINE_RE = re.compile(r'^(JsonNode|POJO),(\d+),(\d+),([0-9.]+),([-0-9.]+),([-0-9.]+),([-0-9.]+),(\d+)$')


def parse_input(path: Path):
    rows = []
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('mode,'):
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        mode, rows_n, millis, rps, mb, ma, md, checksum = m.groups()
        rows.append({
            'mode': mode,
            'rows': int(rows_n),
            'millis': int(millis),
            'rows_per_sec': float(rps),
            'mem_before_mb': float(mb),
            'mem_after_mb': float(ma),
            'mem_delta_mb': float(md),
            'checksum': int(checksum),
        })
    if not rows:
        raise SystemExit(f'No benchmark rows parsed from {path}')
    return rows


def summarize(mode_rows):
    return {
        'n': len(mode_rows),
        'millis_mean': statistics.mean([r['millis'] for r in mode_rows]),
        'millis_std': statistics.pstdev([r['millis'] for r in mode_rows]),
        'rps_mean': statistics.mean([r['rows_per_sec'] for r in mode_rows]),
        'rps_std': statistics.pstdev([r['rows_per_sec'] for r in mode_rows]),
        'mem_delta_mean': statistics.mean([r['mem_delta_mb'] for r in mode_rows]),
        'mem_delta_std': statistics.pstdev([r['mem_delta_mb'] for r in mode_rows]),
    }


def pct(a, b):
    return (a - b) / b * 100.0


def render_md(json_sum, pojo_sum, checksum_ok, out_path: Path):
    rps_gain = pct(pojo_sum['rps_mean'], json_sum['rps_mean'])
    time_gain = pct(json_sum['millis_mean'], pojo_sum['millis_mean'])

    md = f"""# Benchmark Analysis (Auto)

## Summary
- Samples per mode: **{json_sum['n']}**
- Checksum consistency: **{'OK' if checksum_ok else 'MISMATCH'}**

### JsonNode (mean ± std)
- millis: **{json_sum['millis_mean']:.1f} ± {json_sum['millis_std']:.1f} ms**
- rows/s: **{json_sum['rps_mean']:.2f} ± {json_sum['rps_std']:.2f}**
- mem_delta_mb: **{json_sum['mem_delta_mean']:.2f} ± {json_sum['mem_delta_std']:.2f}**

### POJO (mean ± std)
- millis: **{pojo_sum['millis_mean']:.1f} ± {pojo_sum['millis_std']:.1f} ms**
- rows/s: **{pojo_sum['rps_mean']:.2f} ± {pojo_sum['rps_std']:.2f}**
- mem_delta_mb: **{pojo_sum['mem_delta_mean']:.2f} ± {pojo_sum['mem_delta_std']:.2f}**

## Interpretation
- Throughput: **POJO +{rps_gain:.2f}%** vs JsonNode
- Time-to-complete: **POJO {time_gain:.2f}% faster** (lower millis)
- `mem_delta_mb` can be noisy (snapshot delta), so use GC logs/heap dump for memory conclusions.

## Recommendation
- On this machine/run set, **POJO is clearly faster**.
- For memory, use MAT comparison on `.hprof` + GC log metrics (pause sum/p95/p99).
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='raw text or CSV lines containing repeated benchmark rows')
    ap.add_argument('--out', default='out/BENCHMARK_ANALYSIS.md')
    args = ap.parse_args()

    rows = parse_input(Path(args.input))
    json_rows = [r for r in rows if r['mode'] == 'JsonNode']
    pojo_rows = [r for r in rows if r['mode'] == 'POJO']

    if len(json_rows) == 0 or len(pojo_rows) == 0:
        raise SystemExit('Need both JsonNode and POJO rows')

    checksums = {r['checksum'] for r in rows}
    checksum_ok = len(checksums) == 1

    render_md(summarize(json_rows), summarize(pojo_rows), checksum_ok, Path(args.out))
    print(Path(args.out))


if __name__ == '__main__':
    main()
