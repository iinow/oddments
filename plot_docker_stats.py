#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
import matplotlib.pyplot as plt

def to_float_cpu(s: str) -> float:
    return float(s.strip().replace('%',''))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='docker stats csv (ts,cpu,mem_used_mb,mem_limit_mb)')
    ap.add_argument('--out', default='out/docker_cpu_mem_chart.png')
    args = ap.parse_args()

    rows = []
    with open(args.input) as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)

    if not rows:
        raise SystemExit('no rows in stats input')

    t0 = float(rows[0]['ts'])
    xs = [float(r['ts']) - t0 for r in rows]
    cpu = [to_float_cpu(r['cpu']) for r in rows]
    mem = [float(r['mem_used_mb']) for r in rows]

    fig, ax = plt.subplots(1,2, figsize=(12,4))
    ax[0].plot(xs, cpu, color='#4e79a7')
    ax[0].set_title('Container CPU usage (%)')
    ax[0].set_xlabel('seconds')
    ax[0].set_ylabel('%')
    ax[0].grid(alpha=.25)

    ax[1].plot(xs, mem, color='#f28e2b')
    ax[1].set_title('Container memory usage (MB)')
    ax[1].set_xlabel('seconds')
    ax[1].set_ylabel('MB')
    ax[1].grid(alpha=.25)

    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    print(out)

if __name__ == '__main__':
    main()
