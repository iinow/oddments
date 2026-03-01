#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def read_single_csv(path: Path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def read_summary(path: Path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        out[r['mode']] = r
    return out


def read_stats(path: Path):
    cpus = []
    mems = []
    with path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                cpus.append(float(str(row['cpu']).replace('%', '').strip()))
                mems.append(float(row['mem_used_mb']))
            except Exception:
                pass
    if not cpus:
        return None
    return {
        'cpu_avg': sum(cpus)/len(cpus),
        'cpu_peak': max(cpus),
        'mem_avg': sum(mems)/len(mems) if mems else 0.0,
        'mem_peak': max(mems) if mems else 0.0,
        'samples': len(cpus)
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-subdir', required=True)
    ap.add_argument('--out-root', default='out')
    ap.add_argument('--reports-root', default='reports')
    args = ap.parse_args()

    out_dir = Path(args.out_root) / args.out_subdir
    rep_dir = Path(args.reports_root) / args.out_subdir
    rep_dir.mkdir(parents=True, exist_ok=True)

    j = read_single_csv(out_dir / 'jsonnode.csv')
    p = read_single_csv(out_dir / 'pojo.csv')
    sdx = read_single_csv(out_dir / 'simdjson.csv') if (out_dir / 'simdjson.csv').exists() else None
    g = read_summary(out_dir / 'gc_memory_detailed_summary.csv')
    s_json = read_stats(out_dir / 'jsonnode_stats.csv') if (out_dir / 'jsonnode_stats.csv').exists() else None
    s_pojo = read_stats(out_dir / 'pojo_stats.csv') if (out_dir / 'pojo_stats.csv').exists() else None
    s_simd = read_stats(out_dir / 'simdjson_stats.csv') if (out_dir / 'simdjson_stats.csv').exists() else None

    def num(v, d=2):
        try:
            return f"{float(v):.{d}f}"
        except Exception:
            return str(v)

    throughput_gain = (float(p['rows_per_sec']) - float(j['rows_per_sec'])) / float(j['rows_per_sec']) * 100.0
    time_gain_ms = float(j['millis']) - float(p['millis'])

    lines = []
    lines.append(f"# Docker Benchmark Report ({args.out_subdir})\n")
    lines.append("## Single-run benchmark results\n")
    lines.append(f"- JsonNode: {j['millis']} ms, {num(j['rows_per_sec'])} rows/s, mem_delta={num(j['mem_delta_mb'])} MB")
    lines.append(f"- POJO: {p['millis']} ms, {num(p['rows_per_sec'])} rows/s, mem_delta={num(p['mem_delta_mb'])} MB")
    if sdx:
        lines.append(f"- SimdJson: {sdx['millis']} ms, {num(sdx['rows_per_sec'])} rows/s, mem_delta={num(sdx['mem_delta_mb'])} MB\n")
    else:
        lines.append("")
    lines.append(f"- Throughput compare: **POJO {throughput_gain:+.2f}%** vs JsonNode")
    lines.append(f"- Time compare: **POJO faster by {time_gain_ms:.0f} ms**")
    if sdx:
        simd_gain_vs_json = (float(sdx['rows_per_sec']) - float(j['rows_per_sec'])) / float(j['rows_per_sec']) * 100.0
        simd_gain_vs_pojo = (float(sdx['rows_per_sec']) - float(p['rows_per_sec'])) / float(p['rows_per_sec']) * 100.0
        lines.append(f"- SimdJson throughput vs JsonNode: **{simd_gain_vs_json:+.2f}%**")
        lines.append(f"- SimdJson throughput vs POJO: **{simd_gain_vs_pojo:+.2f}%**")
    lines.append("")

    lines.append("## GC summary\n")
    for mode in ['JsonNode', 'POJO', 'SimdJson']:
        row = g.get(mode, {})
        if row:
            lines.append(f"- {mode}: events={row.get('gc_events')}, pause_sum={num(row.get('gc_pause_sum_ms'))} ms, pause_max={num(row.get('gc_pause_max_ms'))} ms, pause_p95={num(row.get('gc_pause_p95_ms'))} ms")

    if s_json or s_pojo or s_simd:
        lines.append("\n## Container CPU/Memory stats (mode-separated)\n")
        if s_json:
            lines.append(f"- JsonNode samples: {s_json['samples']}, CPU avg/peak: **{s_json['cpu_avg']:.2f}% / {s_json['cpu_peak']:.2f}%**, Mem avg/peak: **{s_json['mem_avg']:.2f} / {s_json['mem_peak']:.2f} MB**")
        if s_pojo:
            lines.append(f"- POJO samples: {s_pojo['samples']}, CPU avg/peak: **{s_pojo['cpu_avg']:.2f}% / {s_pojo['cpu_peak']:.2f}%**, Mem avg/peak: **{s_pojo['mem_avg']:.2f} / {s_pojo['mem_peak']:.2f} MB**")
        if s_simd:
            lines.append(f"- SimdJson samples: {s_simd['samples']}, CPU avg/peak: **{s_simd['cpu_avg']:.2f}% / {s_simd['cpu_peak']:.2f}%**, Mem avg/peak: **{s_simd['mem_avg']:.2f} / {s_simd['mem_peak']:.2f} MB**")
        lines.append("")

    lines.append("## Charts\n")
    lines.append("![gc_memory_detailed](./gc_memory_detailed.png)")
    if s_json or s_pojo or s_simd:
        lines.append("![docker_cpu_mem_chart_compare](./docker_cpu_mem_chart_compare.png)")

    if (rep_dir / 'jsonnode.jfr').exists() or (rep_dir / 'pojo.jfr').exists() or (rep_dir / 'simdjson.jfr').exists():
        lines.append("\n## JFR files\n")
        if (rep_dir / 'jsonnode.jfr').exists():
            lines.append("- jsonnode.jfr")
        if (rep_dir / 'pojo.jfr').exists():
            lines.append("- pojo.jfr")
        if (rep_dir / 'simdjson.jfr').exists():
            lines.append("- simdjson.jfr")

    (rep_dir / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(rep_dir / 'REPORT.md')


if __name__ == '__main__':
    main()
