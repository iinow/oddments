#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
import matplotlib.pyplot as plt


def load_stats(path: Path):
    rows = []
    with path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append({
                    'ts': float(row['ts']),
                    'cpu': float(str(row['cpu']).replace('%', '').strip()),
                    'mem': float(row['mem_used_mb'])
                })
            except Exception:
                pass
    if not rows:
        return [], [], []
    t0 = rows[0]['ts']
    xs = [r['ts'] - t0 for r in rows]
    cpu = [r['cpu'] for r in rows]
    mem = [r['mem'] for r in rows]
    return xs, cpu, mem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonnode', required=True, help='jsonnode stats csv')
    ap.add_argument('--pojo', required=True, help='pojo stats csv')
    ap.add_argument('--out', default='out/docker_cpu_mem_chart_compare.png')
    args = ap.parse_args()

    jx, jcpu, jmem = load_stats(Path(args.jsonnode))
    px, pcpu, pmem = load_stats(Path(args.pojo))

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))

    ax[0].plot(jx, jcpu, label='JsonNode', color='#4e79a7')
    ax[0].plot(px, pcpu, label='POJO', color='#f28e2b')
    ax[0].set_title('CPU usage (%) by mode')
    ax[0].set_xlabel('seconds')
    ax[0].set_ylabel('%')
    ax[0].grid(alpha=.25)
    ax[0].legend()

    ax[1].plot(jx, jmem, label='JsonNode', color='#4e79a7')
    ax[1].plot(px, pmem, label='POJO', color='#f28e2b')
    ax[1].set_title('Container memory usage (MB) by mode')
    ax[1].set_xlabel('seconds')
    ax[1].set_ylabel('MB')
    ax[1].grid(alpha=.25)
    ax[1].legend()

    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    print(out)


if __name__ == '__main__':
    main()
