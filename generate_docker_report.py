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
    g = read_summary(out_dir / 'gc_memory_detailed_summary.csv')
    s = read_stats(out_dir / 'docker_stats.csv') if (out_dir / 'docker_stats.csv').exists() else None

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
    lines.append(f"- POJO: {p['millis']} ms, {num(p['rows_per_sec'])} rows/s, mem_delta={num(p['mem_delta_mb'])} MB\n")
    lines.append(f"- Throughput compare: **POJO {throughput_gain:+.2f}%** vs JsonNode")
    lines.append(f"- Time compare: **POJO faster by {time_gain_ms:.0f} ms**\n")

    lines.append("## GC summary\n")
    for mode in ['JsonNode', 'POJO']:
        row = g.get(mode, {})
        if row:
            lines.append(f"- {mode}: events={row.get('gc_events')}, pause_sum={num(row.get('gc_pause_sum_ms'))} ms, pause_max={num(row.get('gc_pause_max_ms'))} ms, pause_p95={num(row.get('gc_pause_p95_ms'))} ms")

    if s:
        lines.append("\n## Container CPU/Memory stats\n")
        lines.append(f"- samples: {s['samples']}")
        lines.append(f"- CPU avg: **{s['cpu_avg']:.2f}%**, CPU peak: **{s['cpu_peak']:.2f}%**")
        lines.append(f"- Mem avg: **{s['mem_avg']:.2f} MB**, Mem peak: **{s['mem_peak']:.2f} MB**\n")

    lines.append("## Charts\n")
    lines.append("![gc_memory_detailed](./gc_memory_detailed.png)")
    if s:
        lines.append("![docker_cpu_mem_chart](./docker_cpu_mem_chart.png)")

    (rep_dir / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    print(rep_dir / 'REPORT.md')


if __name__ == '__main__':
    main()
