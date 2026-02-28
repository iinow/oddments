import argparse
import csv
import re
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

PAUSE_RE = re.compile(
    r"\[(?P<uptime>[0-9.]+)s\].*?\[gc\s*\].*?GC\((?P<id>\d+)\) Pause .*? (?P<before>\d+)M->(?P<after>\d+)M\((?P<heap>\d+)M\) (?P<pause>[0-9.]+)ms"
)
EDEN_RE = re.compile(r"GC\((?P<id>\d+)\) Eden regions: (?P<before>\d+)->(?P<after>\d+)\((?P<target>\d+)\)")
SURV_RE = re.compile(r"GC\((?P<id>\d+)\) Survivor regions: (?P<before>\d+)->(?P<after>\d+)\((?P<target>\d+)\)")
OLD_RE = re.compile(r"GC\((?P<id>\d+)\) Old regions: (?P<before>\d+)->(?P<after>\d+)")


def percentile(values, p):
    if not values:
        return 0.0
    vals = sorted(values)
    k = (len(vals)-1) * p
    f = int(k)
    c = min(f+1, len(vals)-1)
    if f == c:
        return vals[f]
    return vals[f] + (vals[c]-vals[f]) * (k-f)


def parse_gc_log(path: Path):
    gc = {}
    for line in path.read_text(errors="ignore").splitlines():
        m = PAUSE_RE.search(line)
        if m:
            gid = int(m.group("id"))
            gc.setdefault(gid, {})
            gc[gid].update({
                "t": float(m.group("uptime")),
                "before_mb": float(m.group("before")),
                "after_mb": float(m.group("after")),
                "heap_mb": float(m.group("heap")),
                "pause_ms": float(m.group("pause")),
            })
            continue

        for rgx, key in [(EDEN_RE, "eden"), (SURV_RE, "survivor"), (OLD_RE, "old")]:
            m2 = rgx.search(line)
            if m2:
                gid = int(m2.group("id"))
                gc.setdefault(gid, {})
                gc[gid][f"{key}_before"] = float(m2.group("before"))
                gc[gid][f"{key}_after"] = float(m2.group("after"))
                if "target" in m2.groupdict() and m2.group("target") is not None:
                    gc[gid][f"{key}_target"] = float(m2.group("target"))
                break

    points = [v for _, v in sorted(gc.items()) if "pause_ms" in v]
    return points


def load_bench_csv(path: Path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else None


def summary(points):
    pauses = [p["pause_ms"] for p in points]
    return {
        "events": len(points),
        "pause_sum": sum(pauses),
        "pause_max": max(pauses) if pauses else 0.0,
        "pause_p95": percentile(pauses, 0.95),
        "peak_before_mb": max((p["before_mb"] for p in points), default=0.0),
        "peak_after_mb": max((p["after_mb"] for p in points), default=0.0),
        "avg_after_mb": statistics.mean([p["after_mb"] for p in points]) if points else 0.0,
        "peak_old_after": max((p.get("old_after", 0.0) for p in points), default=0.0),
    }


def write_summary_csv(out_path: Path, j_sum, p_sum, j_bench, p_bench):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "mode", "rows", "millis", "rows_per_sec", "mem_delta_mb",
            "gc_events", "gc_pause_sum_ms", "gc_pause_max_ms", "gc_pause_p95_ms",
            "peak_before_mb", "peak_after_mb", "avg_after_mb", "peak_old_after_regions"
        ])
        for mode, s, b in [("JsonNode", j_sum, j_bench), ("POJO", p_sum, p_bench)]:
            w.writerow([
                mode,
                b.get("rows", ""), b.get("millis", ""), b.get("rows_per_sec", ""), b.get("mem_delta_mb", ""),
                f"{s['events']}", f"{s['pause_sum']:.3f}", f"{s['pause_max']:.3f}", f"{s['pause_p95']:.3f}",
                f"{s['peak_before_mb']:.2f}", f"{s['peak_after_mb']:.2f}", f"{s['avg_after_mb']:.2f}", f"{s['peak_old_after']:.2f}"
            ])


def plot(points_j, points_p, out_png: Path):
    out_png.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(2, 2, figsize=(14, 8))

    # before/after heap on pause points
    ax[0][0].plot([p["t"] for p in points_j], [p["before_mb"] for p in points_j], label="JsonNode before", color="#4e79a7")
    ax[0][0].plot([p["t"] for p in points_j], [p["after_mb"] for p in points_j], label="JsonNode after", color="#4e79a7", linestyle="--")
    ax[0][0].plot([p["t"] for p in points_p], [p["before_mb"] for p in points_p], label="POJO before", color="#f28e2b")
    ax[0][0].plot([p["t"] for p in points_p], [p["after_mb"] for p in points_p], label="POJO after", color="#f28e2b", linestyle="--")
    ax[0][0].set_title("Heap before/after each STW")
    ax[0][0].set_xlabel("uptime(s)")
    ax[0][0].set_ylabel("MB")
    ax[0][0].legend(fontsize=8)

    # pause timeline
    ax[0][1].plot([p["t"] for p in points_j], [p["pause_ms"] for p in points_j], label="JsonNode", color="#4e79a7")
    ax[0][1].plot([p["t"] for p in points_p], [p["pause_ms"] for p in points_p], label="POJO", color="#f28e2b")
    ax[0][1].set_title("STW pause timeline")
    ax[0][1].set_xlabel("uptime(s)")
    ax[0][1].set_ylabel("ms")
    ax[0][1].legend()

    # old regions after
    ax[1][0].plot([p["t"] for p in points_j], [p.get("old_after", 0) for p in points_j], label="JsonNode", color="#4e79a7")
    ax[1][0].plot([p["t"] for p in points_p], [p.get("old_after", 0) for p in points_p], label="POJO", color="#f28e2b")
    ax[1][0].set_title("Old regions after GC")
    ax[1][0].set_xlabel("uptime(s)")
    ax[1][0].set_ylabel("regions")
    ax[1][0].legend()

    # cumulative pause
    cum_j, cum_p = [], []
    s = 0.0
    for p in points_j:
        s += p["pause_ms"]
        cum_j.append(s)
    s = 0.0
    for p in points_p:
        s += p["pause_ms"]
        cum_p.append(s)

    ax[1][1].plot([p["t"] for p in points_j], cum_j, label="JsonNode", color="#4e79a7")
    ax[1][1].plot([p["t"] for p in points_p], cum_p, label="POJO", color="#f28e2b")
    ax[1][1].set_title("Cumulative STW pause")
    ax[1][1].set_xlabel("uptime(s)")
    ax[1][1].set_ylabel("ms")
    ax[1][1].legend()

    fig.suptitle("Detailed GC/Memory comparison")
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonnode-gc", required=True)
    ap.add_argument("--pojo-gc", required=True)
    ap.add_argument("--jsonnode-csv", required=True)
    ap.add_argument("--pojo-csv", required=True)
    ap.add_argument("--out-png", default="build/reports/gc_memory_detailed.png")
    ap.add_argument("--out-summary", default="build/reports/gc_memory_detailed_summary.csv")
    args = ap.parse_args()

    points_j = parse_gc_log(Path(args.jsonnode_gc))
    points_p = parse_gc_log(Path(args.pojo_gc))
    j_sum = summary(points_j)
    p_sum = summary(points_p)

    j_bench = load_bench_csv(Path(args.jsonnode_csv)) or {}
    p_bench = load_bench_csv(Path(args.pojo_csv)) or {}

    write_summary_csv(Path(args.out_summary), j_sum, p_sum, j_bench, p_bench)
    plot(points_j, points_p, Path(args.out_png))

    print(Path(args.out_png))
    print(Path(args.out_summary))
    print("JsonNode summary:", j_sum)
    print("POJO summary:", p_sum)


if __name__ == "__main__":
    main()
